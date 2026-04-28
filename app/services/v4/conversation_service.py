import asyncio
import json
import traceback
import time
from asyncio import Future, CancelledError
from typing import Optional, List

from aalp_service_utils.misc.dataclasses import ContentType
from legislation_survey.config import LegislationSurveySettings
from legislation_survey.dataclasses import LegislationSurveyServiceOutput, Summary, RagServiceOutput
from legislation_survey.service import LegislationSurveyService
from billiard.exceptions import SoftTimeLimitExceeded
from common_utils.string_utils import identify_and_remove_html_tags
from common_utils.time_utils import current_time_millis, total_time_millis
from conversation_core.shared.constants import Constants
from conversation_core.shared.dynamo_helper_v2 import ConversationDB as ConversationDBV2
from conversation_core.shared.enums import ConversationActionType
from conversation_core.shared.enums import RetrieveConversationEntryStatuses
from conversation_core.shared.models.answer_profile import AnswerProfile, ActionSequence
from conversation_core.shared.models.errors import ErrorModel
from conversation_core.shared.services.v4.conversation_service_base import ConversationServiceBaseV4
from conversation_core.shared.worker.worker_task import WorkerTask
from datadog_utils import metrics_client
from gcs_utils.entitlement_client import EntitlementClient
from raslogger import LoggingFactory

from config.settings import get_settings, map_to_ls_settings
from models.legislation_survey_result import LegislationSurveyResult
from services.common_services import (get_or_create_eventloop,
                                      get_task_id, log_event_loop_id,
                                      answer_profile_service, get_llm_profile_service,
                                      refresh_auth_token)
from services.email_service import EmailService
from utils.common_util import mock_open_ai_response
from utils.converters import convert_conv_entries_to_aalp_conv_history
from utils.custom_exceptions import MaliciousContentException
from utils.exception_mappings import get_error_code, get_error_message, get_error_retryable

logger = LoggingFactory.get_logger(__name__)
settings = get_settings()
dynamo_db_v2 = ConversationDBV2(settings.DYNAMO_TABLE_NAME, settings.S3_BUCKET, settings.REGION)
email_service = EmailService(ses_secret=settings.AWS_SES_SECRET)


class LegislationSurveyGenerateAnswer(RagServiceOutput):
    ls_result: LegislationSurveyServiceOutput

    def get_results(self):
        results = {
            **self.ls_result.model_dump(exclude_none=True, exclude_unset=True)
        }
        return results



class WestlawGenerateAnswer(RagServiceOutput):
    ls_result: LegislationSurveyServiceOutput
    rag_service_output: RagServiceOutput
    system_output: LegislationSurveyResult

    def get_results(self):
        results = {
            **self.ls_result.model_dump(exclude_none=True, exclude_unset=True)
        }
        return results


class ConversationService(ConversationServiceBaseV4):
    def __init__(self, entitlement_client: EntitlementClient):
        super().__init__(settings=settings,
                         dynamo_db_v2=dynamo_db_v2,
                         email_service=email_service,
                         answer_profile_service=answer_profile_service,
                         entitlement_client=entitlement_client)
        logger.info("Initiated ConversationServiceBase  V4")

    def _suppress_allfeds_answers(self, answers) -> None:
        """
        Suppress ALLFEDS jurisdiction answers by clearing their content.
        Labs wheel generates answer for Fed Cases but this should not be shown to user.
        """
        if answers and isinstance(answers, list):
            for answer in answers:
                if hasattr(answer, 'jurisdiction') and answer.jurisdiction == "ALLFEDS":
                    answer.answer_text = ""
                    answer.cites = []
                    answer.sources = []

    def get_error_details(self, ex: Exception) -> ErrorModel:
        error_model = ErrorModel()
        error_model.is_retryable = get_error_retryable(ex)
        error_model.code = get_error_code(ex)
        error_model.message = get_error_message(ex)
        context = self._get_error_context()
        error_model.user_input = context.get("user_input")
        error_model.jurisdictions = context.get("jurisdictions")
        return error_model

    def handle_error(
            self, user_id: str, conversation_id: str, conversation_entry_id: str, answer_profile: AnswerProfile,
            ex: Exception
    ):
        pass

    def finish_conversation(
            self,
            user_id: str,
            user_input: str,
            conversation_id: str,
            conversation_entry_id: str,
            answer_solution_profile: str,
            overrides: Optional[dict],
            filters: Optional[dict],
            conversation_action_type: ConversationActionType,
            auth_token: str,
            worker_task: WorkerTask,
            additional_user_inputs: Optional[dict] = None,
            tags: Optional[List[str]] = None,
            user_session: dict = None,
            meta_data: dict = None,
            results: any = None,
    ):
        pass

    async def generate_answer(
            self,
            user_id: str,
            user_input: str,
            conversation_id: str,
            conversation_entry_id: str,
            answer_solution_profile: str,
            answer_profile: AnswerProfile,
            jurisdictions: Optional[List[str]],
            content_types: Optional[List[str]],
            content_types_exclude: Optional[List[str]],
            conversation_action_type: ConversationActionType,
            auth_token: str,
            worker_task: WorkerTask,
            task_action_sequence: ActionSequence,
            additional_user_inputs: Optional[dict] = None,
            tags: Optional[List[str]] = None,
            user_session: dict = None,
            meta_data: dict = None,
            conversation_history: List[dict] = None,
    ) -> any:
        start_report_time = time.time()
        estimated_report_duration = self.get_estimated_report_duration(answer_profile=answer_profile)

        worker_task.update_task_status_in_progress(percent_complete=0, status_desc="Legislation Survey task running")

        aalp_config: LegislationSurveySettings = map_to_ls_settings(
            settings=settings,
            auth_token=auth_token,
            solution_profile=answer_profile.rag_solution,
            ras_profile=answer_solution_profile.lower(),
            conversation_id=conversation_id,
            conversation_entry_id=conversation_entry_id,
            answer_profile=answer_profile,
            cobalt_session=user_session,
            tags=tags,
            conversation_type=meta_data["conversation_type"],
            metadata=meta_data,
            llm_profile_service=get_llm_profile_service(),
            user_id=user_id,
        )
        is_initial_conversation = self.is_initial_conversation(user_id=user_id, conversation_id=conversation_id)
        conversation_history = self.get_conversation_history(user_id=user_id, conversation_id=conversation_id,
                                                             include_intermediate_results=True)

        self.update_progress(worker_task, start_report_time, estimated_report_duration)

        # Need to make sure the token is within its TTL, or some calls will fail with 401 Authorization error
        refresh_auth_token(ls_settings=aalp_config,
                           gcs_user_secret=settings.GCS_USER_SECRET)

        if hasattr(answer_profile, "rag_solution_batch_size"):
            rag_solution_batch_size = answer_profile.rag_solution_batch_size
        else:
            rag_solution_batch_size = 3
        aalp_config.content_selection_settings.max_juris_in_a_batch = rag_solution_batch_size

        try:
            logger.info("start generate_answer")
            get_or_create_eventloop()
            mock_open_ai_data = mock_open_ai_response(answer_solution_profile, is_initial_conversation)
            if "prompt injection test case" in user_input.lower():
                raise MaliciousContentException("Prompt injection test case")

            self.update_progress(worker_task, start_report_time, estimated_report_duration)

            logger.info("start generate_answer")
            start_time = current_time_millis()
            metrics_client.send_metric(
                name="RagServiceInitializeDuration", value=total_time_millis(start_time), tags=tags
            )
            if jurisdictions is None:
                jurisdictions = answer_profile.default_fermi_jurisdiction

            logger.debug("start generate_answer task")
            tasks = []
            try:
                task_id = get_task_id()
                task_name = f"generate_answer_ajs_{task_id}"

                include_case_answers = False
                include_related_federal = False
                if additional_user_inputs and isinstance(additional_user_inputs, dict):
                    include_case_answers = additional_user_inputs.get("include_cases", False)
                    logger.info(f"include case answers: {include_case_answers}")

                    include_related_federal = additional_user_inputs.get("include_related_federal", False)
                    logger.info(f"include related federal: {include_related_federal}")

                if include_related_federal:
                    jurisdictions = list(set(jurisdictions + ["ALLFEDS"]))

                generate_answer_task = asyncio.create_task(
                    LegislationSurveyService.generate_answer(
                        profile=answer_profile.rag_solution,
                        settings=aalp_config,
                        question=user_input,
                        include_case_answers=include_case_answers,
                        include_related_federal=include_related_federal,
                        fermi_jurisdictions=jurisdictions,
                        conversation_history=conversation_history,
                        mock_open_ai_data=mock_open_ai_data,
                        worker_task=worker_task
                    )
                )
                self.update_progress(worker_task, start_report_time, estimated_report_duration)
                generate_answer_task.set_name(task_name)
                log_event_loop_id(task_name)
                tasks.append(generate_answer_task)

                logger.debug("awaiting generate answer task")
                future_tasks: Future = asyncio.gather(*tasks)
                while not future_tasks.done() and not future_tasks.cancelled():
                    await asyncio.sleep(5)
                    logger.debug("Waited 5 seconds")
                    conversation_entry = dynamo_db_v2.get_conversation_entry(user_id=user_id,
                                                                             conversation_id=conversation_id,
                                                                             conversation_entry_id=conversation_entry_id)
                    self.update_progress(worker_task, start_report_time, estimated_report_duration)
                    if conversation_entry.status == RetrieveConversationEntryStatuses.CANCELLING.value:
                        logger.info("Celery worker task has been revoked, cancelling asyncio task(s)")
                        for task in tasks:
                            if task and not task.cancelled():
                                task.cancel()
            except Exception as ex:
                logger.error(
                    f"{LegislationSurveyGenerateAnswer.__name__}::{type(ex).__name__} exception occurred {ex} while "
                    f"executing async tasks; {traceback.format_tb(ex.__traceback__)}")
                for task in tasks:
                    if task and not task.cancelled():
                        task.cancel()
                raise ex
            worker_task.update_task_status_in_progress(percent_complete=100,
                                                       status_desc="Legislation Survey task complete")
            logger.info(f"LegislationSurveyService generate answer finished: {total_time_millis(start_time)} ms")

            # Need to make sure the token is within its TTL, or some calls will fail with 401 Authorization error
            refresh_auth_token(ls_settings=aalp_config,
                               gcs_user_secret=settings.GCS_USER_SECRET)

            if generate_answer_task.cancelled():
                raise CancelledError
            else:
                results: LegislationSurveyServiceOutput = generate_answer_task.result()
                latency_st = current_time_millis()
                logger.info(f"TIME TAKEN FOR CITE IS: {current_time_millis() - latency_st}")
                logger.info(f"end generate_answer - total time taken: {total_time_millis(start_time)} ms")

                # FIXME: This is a temporary fix as DO requires summary to be exist and be populated
                results.summary = Summary(summary_text="Placeholder text, as this field is required by DO",
                                          cites=[])
                for answer in results.answers:
                    answer.content_type = None
                if "case_answers" in results:
                    for answer in results.case_answers:
                        answer.content_type = None

                # Labs wheel generates case answers for ALLFEDS but this should not be shown to user.
                # Suppressing it here
                self._suppress_allfeds_answers(getattr(results, 'federal_case_answers', None))
                self._suppress_allfeds_answers(getattr(results, 'case_answers', None))

                return LegislationSurveyGenerateAnswer(ls_result=results)
        except CancelledError as cancel_ex:
            dynamo_db_v2.update_conversation_entry(
                user_id=user_id,
                conversation_id=conversation_id,
                conversation_entry_id=conversation_entry_id,
                attribute_updates={Constants.CONV_STATUS: RetrieveConversationEntryStatuses.CANCELLED.value}
            )
            logger.info(f"Conversation Entry Status set to {RetrieveConversationEntryStatuses.CANCELLED.value}")
            raise cancel_ex
        except SoftTimeLimitExceeded as soft_timeout_ex:
            logger.warn(f"Soft timeout exceeded for conversation entry - {aalp_config.conversation_entry_id}.")
            raise soft_timeout_ex

    def get_system_output(self, results: any, answer_profile: AnswerProfile) -> any:
        return results.get_results()

    def get_intermediate_results_dict(self, results: any) -> dict:
        return results.get_results()

    def get_answer_text(self, results: any) -> str:
        return json.dumps(results.get_results())

    def get_user_input(self, results: any) -> str:
        return results.ls_result.user_input

    def get_conversation_history(self, user_id: str, conversation_id: str, include_intermediate_results: bool) \
            -> list[dict]:
        conversation_history: list[dict] = []
        conversation_entries = self.get_conversation_entries(user_id=user_id,
                                                             conversation_id=conversation_id,
                                                             include_intermediate_results=include_intermediate_results)
        if conversation_entries:
            conversation_history = convert_conv_entries_to_aalp_conv_history(
                conversation_entries=conversation_entries,
                rag_model="RagServiceOutput")
        return conversation_history

    def check_results_for_html(self, results):
        answer_text = ""
        for answer in results.ls_result.answers:
            answer_text += answer.answer_text + "\n"
        has_html, sanitized_text, tags = identify_and_remove_html_tags(answer_text)
        if has_html:
            raise Exception(f"HTML tags found in answer: {tags}. Invalidating this answer and returning a failure.")

    def update_progress(self, worker_task: WorkerTask, start_time: float, estimated_report_duration: Optional[float]):
        if not estimated_report_duration is None:
            worker_task.update_task_status_in_progress(
                percent_complete=WorkerTask.calculate_duration_percent_complete(
                    expected_duration=estimated_report_duration,
                    start_time=start_time,
                    now=time.time()
                ),
                status_desc="Legislation Survey task running"
            )
