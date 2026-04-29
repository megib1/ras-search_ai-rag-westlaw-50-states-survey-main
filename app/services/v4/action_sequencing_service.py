import traceback
from typing import List, Optional

from conversation_core.shared.dynamo_helper_v2 import ConversationDB as ConversationDBV2
from conversation_core.shared.enums import AalpSkill, ConversationActionType
from conversation_core.shared.models.answer_profile import ActionSequence
from conversation_core.shared.models.v2.conversation_entry import CustomMetadata as ConversationEntryCustomMetadata
from conversation_core.shared.services.v4.action_sequencing_service_base import ActionSequenceServiceBaseV4
from conversation_core.shared.worker.worker_task import WorkerTask
from raslogger import LoggingFactory

from config.settings import get_settings
from services.common_services import answer_profile_service, get_entitlement_client
from services.email_service import EmailService
from services.v4.conversation_service import ConversationService
from services.v4.validation_service import ValidationService

logger = LoggingFactory.get_logger(__name__)
settings = get_settings()
entitlement_client = get_entitlement_client(gcs_url=settings.GCS_URL, region=settings.REGION)
dynamo_db_v2 = ConversationDBV2(settings.DYNAMO_TABLE_NAME, settings.S3_BUCKET, settings.REGION)
email_service = EmailService(ses_secret=settings.AWS_SES_SECRET)

validation_service = ValidationService()
conversation_service = ConversationService(entitlement_client=entitlement_client)

rag_worker_services = {
    ConversationActionType.VALIDATION: validation_service,
    ConversationActionType.RAG: conversation_service
}


class ActionSequenceService(ActionSequenceServiceBaseV4):
    def __init__(self):
        super().__init__(settings=settings,
                         dynamo_db_v2=dynamo_db_v2,
                         answer_profile_service=answer_profile_service,
                         worker_services=rag_worker_services,
                         entitlement_client=entitlement_client,
                         email_service=email_service)

    def run_service_action(self,
                           user_id: str,
                           user_input: str,
                           answer_solution_profile: str,
                           overrides: Optional[dict],
                           filters: Optional[dict],
                           conversation_id: str,
                           conversation_entry_id: str,
                           auth_token: str,
                           worker_task: WorkerTask,
                           task_action_sequence: ActionSequence,
                           additional_user_inputs: Optional[dict] = None,
                           user_session: Optional[dict] = None,
                           meta_data: Optional[dict] = None,
                           conversation_entry_metadata: Optional[ConversationEntryCustomMetadata] = None,
                           subscribed_skills: Optional[List[AalpSkill]] = None) -> int:
        try:
            if task_action_sequence.action == ConversationActionType.VALIDATION:
                sequence_result = validation_service.run_validation(
                    user_id=user_id,
                    user_input=user_input,
                    additional_user_inputs=additional_user_inputs,
                    answer_solution_profile=answer_solution_profile,
                    overrides=overrides,
                    filters=filters,
                    conversation_id=conversation_id,
                    conversation_entry_id=conversation_entry_id,
                    conversation_action_type=task_action_sequence.action,
                    auth_token=auth_token,
                    worker_task=worker_task,
                    task_action_sequence=task_action_sequence,
                    user_session=user_session,
                    meta_data=meta_data)
            elif task_action_sequence.action == ConversationActionType.RAG:
                sequence_result = conversation_service.start_or_continue_conversation(
                    user_id=user_id,
                    user_input=user_input,
                    additional_user_inputs=additional_user_inputs,
                    answer_solution_profile=answer_solution_profile,
                    overrides=overrides,
                    filters=filters,
                    conversation_id=conversation_id,
                    conversation_entry_id=conversation_entry_id,
                    conversation_action_type=task_action_sequence.action,
                    auth_token=auth_token,
                    worker_task=worker_task,
                    task_action_sequence=task_action_sequence,
                    user_session=user_session,
                    meta_data=meta_data)
            else:
                raise NotImplementedError("This action type is not supported in this worker!")

            return sequence_result
        except Exception as ex:
            logger.error(f"{ActionSequenceService.__name__}::{type(ex).__name__} exception occurred {ex} while "
                         f"executing {task_action_sequence.action} tasks; {traceback.format_tb(ex.__traceback__)}")
            raise ex