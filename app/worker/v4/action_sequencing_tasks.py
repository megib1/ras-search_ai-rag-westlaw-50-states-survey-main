import sys
from typing import Optional, List

from celery import shared_task, Task
from conversation_core.shared.models.answer_profile import ActionSequence
from conversation_core.cobalt.utils import add_to_span
from conversation_core.shared.dynamo_helper_v2 import ConversationDB as ConversationDBV2
from conversation_core.shared.constants import Constants
from conversation_core.shared.tasks.v4.action_sequencing_tasks_base import ActionSequenceTaskBaseV4, send_metrics
from conversation_core.shared.tasks.v4.task_contracts import ActionSequencingTasks
from conversation_core.shared.utils.action_sequence_util import ActionSequenceUtil
from conversation_core.shared.enums import AalpSkill
from conversation_core.shared.models.v2.conversation_entry import ConversationEntryMetadata
from ddtrace import Span
from raslogger import LoggingFactory

from config.settings import get_settings
from services.common_services import get_entitlement_client, answer_profile_service
from services.v4.action_sequencing_service import ActionSequenceService

logger = LoggingFactory.get_logger(__name__)
settings = get_settings()
entitlement_client = get_entitlement_client(gcs_url=settings.GCS_URL)
action_sequencing_service = ActionSequenceService()
dynamo_db_v2 = ConversationDBV2(settings.DYNAMO_TABLE_NAME, settings.S3_BUCKET, settings.REGION)
action_sequence_util = ActionSequenceUtil(settings=settings,
                                          dynamo_db_v2=dynamo_db_v2,
                                          answer_profile_service=answer_profile_service)


class ActionSequencingTaskV4(ActionSequencingTasks, Task):
    @shared_task(bind=True,
                 retry_backoff=True,
                 retry_kwargs={"max_retries": 1},
                 name=Constants.START_ACTION_SEQUENCE)
    def start_next_action_task(self,
                               user_id: str,
                               user_input: str,
                               answer_solution_profile: str,
                               additional_user_inputs: Optional[dict],
                               overrides: Optional[dict],
                               filters: Optional[dict],
                               conversation_id: str,
                               auth_token: str,
                               task_action_sequence: ActionSequence,
                               action_sequences: List[ActionSequence],
                               user_session: Optional[dict] = None,
                               meta_data: Optional[dict] = None,
                               conversation_entry_metadata: Optional[ConversationEntryMetadata] = None,
                               subscribed_skills: Optional[List[AalpSkill]] = None,
                               route_to_green: bool = False):
        result = ActionSequenceTaskImpl().start_next_action_task(
            task=self,
            user_id=user_id,
            user_input=user_input,
            additional_user_inputs=additional_user_inputs,
            answer_solution_profile=answer_solution_profile,
            overrides=overrides,
            filters=filters,
            conversation_id=conversation_id,
            task_action_sequence=task_action_sequence,
            action_sequences=action_sequences,
            auth_token=auth_token,
            user_session=user_session,
            meta_data=meta_data,
            conversation_entry_metadata=conversation_entry_metadata,
            subscribed_skills=subscribed_skills,
            route_to_green=route_to_green
        )
        return result


def finish_task(span: Span,
                conversation_id: str,
                conversation_entry_id: str,
                answer_solution_profile: str,
                total_queued_time: float,
                total_execution_time: float,
                response_status_code: int,
                user_classification: str):
    send_metrics(conversation_id=conversation_id,
                 conversation_entry_id=conversation_entry_id,
                 answer_solution_profile=answer_solution_profile,
                 total_queued_time=total_queued_time,
                 total_execution_time=total_execution_time,
                 success=False,
                 user_classification=user_classification)

    add_to_span('http.status_code', f'{response_status_code}')
    span.set_exc_info(*sys.exc_info())


class ActionSequenceTaskImpl(ActionSequenceTaskBaseV4):
    def __init__(self):
        super().__init__(
            settings=settings,
            dynamo_db_v2=dynamo_db_v2,
            entitlement_client=entitlement_client,
            action_sequence_util=action_sequence_util,
            action_sequencing_service=action_sequencing_service,
            rag_service_wheel_name="labs-aalp-jurisdictional-survey-service"
        )

    def get_task_implementation(self) -> ActionSequencingTaskV4:
        return ActionSequencingTaskV4()