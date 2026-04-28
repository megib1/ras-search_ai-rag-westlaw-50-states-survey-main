from asyncio import CancelledError
from typing import List, Any, Optional

import requests
from requests import Response
from configuration_utils.constants import Constants as ConfigConstants
from conversation_core.shared.constants import Constants, AnnotationType
from conversation_core.shared.dynamo_helper_v2 import ConversationDB as ConversationDBV2
from conversation_core.shared.enums import RetrieveConversationEntryStatuses, ConversationActionType
from conversation_core.shared.models.answer_profile import AnswerProfile, ActionSequence
from conversation_core.shared.services.v4.validation_service_base import ValidationServiceBaseV4
from conversation_core.shared.worker.worker_task import WorkerTask
from raslogger import LoggingFactory

from config.settings import get_settings
from services.common_services import answer_profile_service, get_entitlement_client

logger = LoggingFactory.get_logger(__name__)
settings = get_settings()
dynamo_db_v2 = ConversationDBV2(settings.DYNAMO_TABLE_NAME, settings.S3_BUCKET, settings.REGION)
entitlement_client = get_entitlement_client(gcs_url=settings.GCS_URL)


class ValidationService(ValidationServiceBaseV4):
    def __init__(self):
        super().__init__(settings=settings,
                         dynamo_db_v2=dynamo_db_v2,
                         answer_profile_service=answer_profile_service,
                         entitlement_client=entitlement_client)

    def do_validation(self,
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
                      task_action_sequence: ActionSequence,
                      additional_user_inputs: Optional[dict] = None,
                      tags: Optional[List[str]] = None,
                      user_session: dict = None,
                      meta_data: dict = None
                      ) -> Any:
        try:
            response = self.call_request_evaluator(auth_token=auth_token,
                                                   user_session=user_session,
                                                   user_input=user_input,
                                                   answer_solution_profile=answer_solution_profile,
                                                   task_action_sequence=task_action_sequence)
            return response.json()
        except CancelledError as cancel_error:
            dynamo_db_v2.update_conversation_entry(
                user_id=user_id,
                conversation_id=conversation_id,
                conversation_entry_id=conversation_entry_id,
                attribute_updates={Constants.CONV_STATUS: RetrieveConversationEntryStatuses.CANCELLED.value}
            )
            logger.info(f"Conversation Entry Status set to {RetrieveConversationEntryStatuses.CANCELLED.value}")
            raise cancel_error

    @staticmethod
    def call_request_evaluator(auth_token: str, user_session: dict, user_input: str, answer_solution_profile: str,
                               task_action_sequence: ActionSequence) -> Response:

        validation_url = f"{settings.AI_CONVERSATIONS_URL}/api/v1/common/input-validation"
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
            "x-tr-product-name": user_session.get(ConfigConstants.SESSION_PRODUCT_NAME, "unknown"),
            "x-tr-product-view": user_session.get(ConfigConstants.SESSION_PRODUCT_VIEW, "unknown"),
        }
        body = {
            "user_input": user_input,
            "answer_solution_profile": answer_solution_profile,
            "pipeline_name": task_action_sequence.pipeline
        }
        response = requests.post(validation_url, json=body, headers=headers)
        return response

    def is_validation_sufficient_to_submit(self,
                                           validation_response: Any,
                                           profile: AnswerProfile,
                                           meta_data: dict) -> bool:
        if "system_output" in validation_response:
            if "annotations" in validation_response["system_output"]:
                for annotation in validation_response["system_output"]["annotations"]:
                    if annotation["type"] == AnnotationType.ADVERSARIAL and annotation["value"]:
                        return False
                    if annotation["type"] == AnnotationType.QUERY_VALIDATION_ERROR:
                        return False
                    if annotation["type"] == AnnotationType.INCOMPLETE and annotation["value"]:
                        return False
                return True
        logger.warning("Could not parse annotations from validation response:\n" + str(validation_response))
        return False

    def handle_error(
            self,
            user_id: str,
            conversation_id: str,
            conversation_entry_id: str,
            answer_profile: AnswerProfile,
            meta_data: dict,
            ex: Exception,
    ):
        # TODO: Implement this
        pass