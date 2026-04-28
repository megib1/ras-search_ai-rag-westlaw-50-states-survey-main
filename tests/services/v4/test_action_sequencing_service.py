import uuid
from unittest.mock import patch, MagicMock, ANY

import pytest
from celery.app.task import Context
from celery.contrib.abortable import AbortableTask
from celery.utils.threads import LocalStack
from conversation_core.shared.models.v2.conversation import Conversation
from conversation_core.shared.models.v2.conversation_entry import ConversationEntry
from conversation_core.shared.models.answer_profile import AnswerProfile, ActionSequence
from conversation_core.shared.enums import (
    ConversationActionType,
    IntentClassification,
    RetrieveConversationEntryStatuses
)

test_user_id = "user_id"
test_user_input = "Will this test pass?"
test_conversation_id = "conversation_id"
test_conversation_entry_id = "conversation_entry_id"
test_validation_entry_id = "validation_entry_id"
test_rag_entry_id = "rag_entry_id"
test_auth_token = "auth_token"


class TestActionSequencingService:
    @pytest.fixture
    def action_sequencing_service(self, mock_conversation_db_v2_instance):
        from services.v4.action_sequencing_service import ActionSequenceService

        return ActionSequenceService()

    @pytest.fixture
    def mock_worker_task(self):
        mock_worker_task = MagicMock()
        mock_worker_task.get_header_value.return_value = "user_classification"
        mock_worker_task.task = AbortableTask()
        mock_worker_task.task.request_stack = LocalStack()
        mock_worker_task.task.request_stack.push(Context(headers={}))
        return mock_worker_task

    @pytest.fixture
    def profile(self):
        answer_profile = AnswerProfile(
            name="westlaw_chat_profile14",
            default_fermi_jurisdiction=["ALLCASES"],
            rag_solution="wl-legislation-survey-v02_4",
            default_result_size=1000,
            sender_addr="Westlaw@Westlaw.com",
            intent_profile="wl-intent-resolver-v006",
            auto_submit_intent_classifications=[IntentClassification.LEGAL, IntentClassification.ILLEGAL_INFORMATION],
            additionalProfileMeta={"max_entries_per_conversation": 2,
                                   "max_conversation_time_hours": 24,
                                   "allowed_meta_data_fields_key": "WL_META_DATA_FIELDS",
                                   "supported_answer_content_types": ['CASE', 'STATUTE', 'REGULATION', 'KNOWHOW',
                                                                      'ANALYTICAL']},
            action_sequence=[
                ActionSequence(initial_action=True,
                               action=ConversationActionType.VALIDATION,
                               pipeline="wl-common-ir-validate-v001",
                               next_action=ConversationActionType.SKILL_ROUTER),
                ActionSequence(action=ConversationActionType.RAG,
                               pipeline="wl-legislation-survey-v02_4",
                               next_action=ConversationActionType.END)
            ]

        )
        answer_profile.include_additional_content_snippets = False
        return answer_profile

    class TestActionSequencingService:
        @pytest.mark.asyncio
        @patch("services.v4.action_sequencing_service.validation_service")
        async def test_run_service_action_validation(
                self, mock_validation_service, action_sequencing_service, profile, mock_worker_task,
                mock_profile_service_instance, mock_conversation_db_v2_instance
        ):
            mock_validation_service.run_validation.return_value = 200
            validation_action_sequence = profile.action_sequence[0]
            mock_profile_service_instance.return_value = profile
            mock_conversation_db_result = Conversation(
                user_id=test_user_id,
                conversation_id=test_conversation_id,
                metadata=None,
                conversation_entries=[]
            )
            mock_conversation_db_v2_instance.get_conversation.return_value = mock_conversation_db_result
            mock_conversation_db_v2_instance.is_conversation_entry_cached.return_value = False

            actual_action_sequencing_result = action_sequencing_service.run_service_action(
                user_id=test_user_id,
                user_input=test_user_input,
                answer_solution_profile=profile.name,
                additional_user_inputs={},
                overrides={},
                filters={},
                conversation_id=test_conversation_id,
                conversation_entry_id=test_conversation_entry_id,
                auth_token=test_auth_token,
                worker_task=mock_worker_task,
                task_action_sequence=validation_action_sequence,
                user_session={},
                meta_data={}
            )

            assert 200 == actual_action_sequencing_result

            mock_validation_service.run_validation.assert_called_once_with(
                user_id=test_user_id,
                user_input=test_user_input,
                conversation_id=test_conversation_id,
                conversation_entry_id=test_conversation_entry_id,
                answer_solution_profile=profile.name,
                additional_user_inputs={},
                overrides={},
                filters={},
                conversation_action_type=ConversationActionType.VALIDATION,
                auth_token=test_auth_token,
                worker_task=mock_worker_task,
                task_action_sequence=validation_action_sequence,
                user_session={},
                meta_data={}
            )

        @pytest.mark.asyncio
        @patch("services.v4.action_sequencing_service.conversation_service")
        async def test_run_service_action_rag(
                self, mock_conversation_service, action_sequencing_service, profile, mock_worker_task,
                mock_profile_service_instance, mock_conversation_db_v2_instance
        ):
            mock_conversation_service.start_or_continue_conversation.return_value = 200
            rag_action_sequence = profile.action_sequence[1]
            mock_profile_service_instance.return_value = profile
            mock_conversation_db_result = Conversation(
                user_id=test_user_id,
                conversation_id=test_conversation_id,
                metadata=None,
                conversation_entries=[ConversationEntry(conversation_entry_id=test_validation_entry_id,
                                                        conversation_entry_metadata={},
                                                        conversation_action_type=ConversationActionType.VALIDATION)]
            )
            mock_conversation_db_v2_instance.get_conversation.return_value = mock_conversation_db_result
            mock_conversation_db_v2_instance.is_conversation_entry_cached.return_value = False

            actual_action_sequencing_result = action_sequencing_service.run_service_action(
                user_id=test_user_id,
                user_input=test_user_input,
                answer_solution_profile=profile.name,
                additional_user_inputs={},
                overrides={},
                filters={},
                conversation_id=test_conversation_id,
                conversation_entry_id=test_conversation_entry_id,
                auth_token=test_auth_token,
                worker_task=mock_worker_task,
                task_action_sequence=rag_action_sequence,
                user_session={},
                meta_data={}
            )

            assert 200 == actual_action_sequencing_result

            mock_conversation_service.start_or_continue_conversation.assert_called_once_with(
                user_id=test_user_id,
                user_input=test_user_input,
                conversation_id=test_conversation_id,
                conversation_entry_id=test_conversation_entry_id,
                answer_solution_profile=profile.name,
                additional_user_inputs={},
                overrides={},
                filters={},
                conversation_action_type=ConversationActionType.RAG,
                auth_token=test_auth_token,
                worker_task=mock_worker_task,
                task_action_sequence=rag_action_sequence,
                user_session={},
                meta_data={}
            )
