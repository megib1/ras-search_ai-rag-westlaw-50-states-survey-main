from asyncio import CancelledError
from unittest import mock

import pytest
from celery.app.task import Context
from celery.contrib.abortable import AbortableTask
from celery.utils.threads import LocalStack
from conversation_core.shared.constants import AnnotationType
from conversation_core.shared.enums import ConversationActionType, IntentClassification
from conversation_core.shared.models.answer_profile import ActionSequence, AnswerProfile

test_user_id = "user_id"
test_user_input = "Will this test pass?"
test_conversation_id = "conversation_id"
test_conversation_entry_id = "conversation_entry_id"
test_auth_token = "auth_token"


class TestValidationService:
    @pytest.fixture
    def validation_service(self, mock_conversation_db_v2_instance):
        from services.v4.validation_service import ValidationService

        return ValidationService()

    @pytest.fixture
    def mock_worker_task(self):
        mock_worker_task = mock.MagicMock()
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
            rag_solution="wl-rag-v054",
            default_result_size=1000,
            sender_addr="Westlaw@Westlaw.com",
            intent_profile="wl-intent-resolver-v005b",
            auto_submit_intent_classifications=[IntentClassification.LEGAL, IntentClassification.ILLEGAL_INFORMATION],
            additionalProfileMeta={
                "max_entries_per_conversation": 2,
                "max_conversation_time_hours": 24,
                "allowed_meta_data_fields_key": "WL_META_DATA_FIELDS",
                "supported_answer_content_types": ["CASE", "STATUTE", "REGULATION", "KNOWHOW", "ANALYTICAL"],
            },
            action_sequence=[
                ActionSequence(
                    initial_action=True,
                    action=ConversationActionType.VALIDATION,
                    pipeline="wl-common-ir-validate-v001",
                    next_action=ConversationActionType.SKILL_ROUTER,
                ),
                ActionSequence(
                    action=ConversationActionType.SKILL_ROUTER,
                    pipeline="wl-common-ir-detect-skills-v001",
                    next_action=ConversationActionType.INTENT,
                    follow_up_enabled=False,
                ),
                ActionSequence(
                    action=ConversationActionType.INTENT,
                    pipeline="wl-intent-resolver-v005b",
                    next_action=ConversationActionType.RAG,
                ),
                ActionSequence(
                    action=ConversationActionType.RAG, pipeline="wl-rag-v054", next_action=ConversationActionType.END
                ),
            ],
        )
        answer_profile.include_additional_content_snippets = False
        return answer_profile

    class TestDoValidation:
        @pytest.mark.asyncio
        @mock.patch("requests.post")
        async def test_do_validation(self, mock_post, validation_service, profile, mock_worker_task):
            expected_validation_response = {
                "system_output": {
                    "annotations": [
                        {"type": "ADVERSARIAL", "value": False},
                        {"type": "QUERY_VALIDATION_ERROR", "value": False},
                        {"type": "INCOMPLETE", "value": False},
                    ]
                }
            }
            mock_response = mock.MagicMock()
            mock_response.json.return_value = expected_validation_response
            mock_post.return_value = mock_response

            validation_action_sequence = profile.action_sequence[0]

            actual_validation_result = validation_service.do_validation(
                user_id=test_user_id,
                user_input=test_user_input,
                conversation_id=test_conversation_id,
                conversation_entry_id=test_conversation_entry_id,
                answer_solution_profile=profile.rag_solution,
                overrides={},
                filters={},
                conversation_action_type=ConversationActionType.VALIDATION,
                auth_token=test_auth_token,
                worker_task=mock_worker_task,
                task_action_sequence=validation_action_sequence,
                user_session={},
                meta_data={},
            )

            assert expected_validation_response == actual_validation_result
            mock_post.assert_called_once()

            is_validation_sufficient_response = validation_service.is_validation_sufficient_to_submit(
                validation_response=actual_validation_result, profile=profile, meta_data={}
            )
            assert is_validation_sufficient_response is True

        @mock.patch("requests.post")
        def test_do_validation_cancelled_error_updates_status_and_reraises(
            self, mock_post, validation_service, profile, mock_worker_task, mock_conversation_db_v2_instance
        ):
            mock_post.side_effect = CancelledError()

            with pytest.raises(CancelledError):
                validation_service.do_validation(
                    user_id=test_user_id,
                    user_input=test_user_input,
                    conversation_id=test_conversation_id,
                    conversation_entry_id=test_conversation_entry_id,
                    answer_solution_profile=profile.rag_solution,
                    overrides={},
                    filters={},
                    conversation_action_type=ConversationActionType.VALIDATION,
                    auth_token=test_auth_token,
                    worker_task=mock_worker_task,
                    task_action_sequence=profile.action_sequence[0],
                    user_session={},
                    meta_data={},
                )

            mock_conversation_db_v2_instance.update_conversation_entry.assert_called_once_with(
                user_id=test_user_id,
                conversation_id=test_conversation_id,
                conversation_entry_id=test_conversation_entry_id,
                attribute_updates=mock.ANY,
            )

    class TestIsValidationSufficientToSubmit:
        @pytest.mark.parametrize(
            ("annotations", "expected"),
            [
                pytest.param(
                    [{"type": AnnotationType.ADVERSARIAL, "value": True}], False, id="adversarial_true_returns_false"
                ),
                pytest.param(
                    [{"type": AnnotationType.QUERY_VALIDATION_ERROR, "value": False}],
                    False,
                    id="query_validation_error_returns_false",
                ),
                pytest.param(
                    [{"type": AnnotationType.INCOMPLETE, "value": True}], False, id="incomplete_true_returns_false"
                ),
            ],
        )
        def test_annotation_branch_returns_false(self, validation_service, profile, annotations, expected):
            result = validation_service.is_validation_sufficient_to_submit(
                validation_response={"system_output": {"annotations": annotations}}, profile=profile, meta_data={}
            )
            assert result is expected

        def test_no_system_output_returns_false(self, validation_service, profile):
            result = validation_service.is_validation_sufficient_to_submit(
                validation_response={"other_key": "value"}, profile=profile, meta_data={}
            )
            assert result is False, "Should return False when system_output key is absent"

    class TestHandleError:
        def test_handle_error_does_not_raise(self, validation_service, profile):
            validation_service.handle_error(
                user_id=test_user_id,
                conversation_id=test_conversation_id,
                conversation_entry_id=test_conversation_entry_id,
                answer_profile=profile,
                meta_data={},
                ex=Exception("test error"),
            )
