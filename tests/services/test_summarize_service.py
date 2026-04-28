# import pytest
#
# from unittest.mock import patch, MagicMock, call
#
# from aalp_service.v2.ask_keycite.config import AskKeyCiteSettings
# from aalp_service.v2.ask_keycite.dataclasses import AskKeyCiteServiceOutput
# from celery.contrib.abortable import AbortableTask
# from celery.utils.threads import LocalStack
# from conversation_core.cobalt.profiles import config_lookup, SupportedAnswerConfigurations
# from conversation_core.shared.constants import Constants
# from conversation_core.shared.enums import ConversationActionType, RetrieveConversationEntryStatuses
# from conversation_core.shared.models.conversation import ConversationEntryResult
#
# from app.utils.custom_exceptions import MaliciousContentException
#
# test_user_id = 'user_id'
# test_legacy_id = 'legacy_id'
# test_headnote_id = 'headnote_id'
# test_conversation_id = 'conversation_id'
# test_conversation_entry_id = 'conversation_entry_id'
# test_auth_token = 'auth_token'
#
#
# class TestSummarizeService:
#
#     @pytest.fixture
#     def summarize_service(self, mock_conversation_db_v2_instance):
#         from app.services.summarize_service import SummarizeService
#         return SummarizeService()
#
#     class TestSummarize:
#
#         @pytest.fixture
#         def mock_worker_task(self):
#             mock_worker_task = MagicMock()
#             mock_worker_task.get_header_value.return_value = 'user_classification'
#             mock_worker_task.task = AbortableTask()
#             mock_worker_task.task.request_stack = LocalStack()
#             return mock_worker_task
#
#         @patch("aalp_service.v2.ask_keycite.service.AskKeyCiteService.generate_answer")
#         @patch("app.services.summarize_service.map_to_ask_keycite_settings")
#         @patch("time.time", lambda: 1.0)
#         def test_summarize(
#                 self,
#                 mock_map_to_ask_keycite_settings,
#                 mock_generate_answer,
#                 mock_worker_task,
#                 mock_conversation_db_v2_instance,
#                 mock_profile_service_instance,
#                 summarize_service,
#         ):
#             profile = config_lookup[SupportedAnswerConfigurations.WL_50SS_LABS_CHAT3]
#             mock_profile_service_instance.get_profile.return_value = profile
#
#             ask_keycite_settings = AskKeyCiteSettings()
#             mock_map_to_ask_keycite_settings.return_value = ask_keycite_settings
#
#             ask_keycite_output = AskKeyCiteServiceOutput(summary={"summarySections": [], "citingReferences": []})
#             mock_generate_answer.return_value = ask_keycite_output
#
#             expected_conversation_entry_result = ConversationEntryResult(
#                 answer_solution_profile=SupportedAnswerConfigurations.WL_50SS_LABS_CHAT3,
#                 jurisdictions=None,
#                 system_output=ask_keycite_output.dict(exclude_none=True),
#                 conversation_action_type=ConversationActionType.RAG,
#                 timestamp=1,
#                 result_viewed=False,
#                 result_viewed_timestamp=0,
#             )
#
#             actual_summarize_result = summarize_service.summarize(
#                 user_id=test_user_id,
#                 legacy_id=test_legacy_id,
#                 headnote_id=test_headnote_id,
#                 answer_solution_profile=SupportedAnswerConfigurations.WL_50SS_LABS_CHAT3,
#                 citing_case_ids=[],
#                 conversation_id=test_conversation_id,
#                 conversation_entry_id=test_conversation_entry_id,
#                 conversation_action_type=ConversationActionType.RAG,
#                 auth_token=test_auth_token,
#                 worker_task=mock_worker_task,
#                 cobalt_session={"sessionId": "test_session_id"},
#             )
#
#             assert actual_summarize_result
#             mock_worker_task.update_task_status_in_progress.assert_called_once_with(0, "Worker started")
#             mock_profile_service_instance.get_profile.assert_called_once_with(
#                 name=SupportedAnswerConfigurations.WL_50SS_LABS_CHAT3
#             )
#             mock_conversation_db_v2_instance.update_conversation_entry.assert_called_once_with(
#                 user_id=test_user_id,
#                 conversation_id=test_conversation_id,
#                 conversation_entry_id=test_conversation_entry_id,
#                 attribute_updates={
#                     Constants.CONV_STATUS: RetrieveConversationEntryStatuses.IN_PROGRESS.value,
#                 },
#             )
#             mock_generate_answer.assert_called_once_with(
#                 profile=profile.rag_solution,
#                 legacy_id=test_legacy_id,
#                 headnote_id=test_headnote_id,
#                 citing_case_ids=[],
#                 jurisdictions=[],
#                 content_types=["PRIMARY_HEADNOTE_PASSAGE", "PRIMARY_HEADNOTE", "CASE"],
#                 prompt_templates=[],
#                 settings=ask_keycite_settings,
#             )
#             mock_conversation_db_v2_instance.complete_conversation_entry.assert_called_once_with(
#                 user_id=test_user_id,
#                 conversation_id=test_conversation_id,
#                 conversation_entry_id=test_conversation_entry_id,
#                 retrieve_conversation_entry_status=RetrieveConversationEntryStatuses.COMPLETE,
#                 result=expected_conversation_entry_result,
#                 intermediate_result={"results": "N/A"},
#             )
#
#         @patch('aalp_service.v2.ask_keycite.service.AskKeyCiteService.generate_answer')
#         @patch('app.services.summarize_service.get_chat_profile')
#         @patch('app.services.summarize_service.map_to_ask_keycite_settings')
#         @patch('time.time', lambda: 1.0)
#         def test_summarize_should_fail_when_malicious_content(self, mock_map_to_ask_keycite_settings,
#                                                               mock_get_chat_profile, mock_generate_answer,
#                                                               mock_worker_task, mock_conversation_db_v2_instance,
#                                                               summarize_service):
#             expected_generate_answer_error = 'MC error'
#             mock_generate_answer.side_effect = MaliciousContentException(expected_generate_answer_error)
#
#             profile = config_lookup[SupportedAnswerConfigurations.WL_50SS_LABS_CHAT3]
#             mock_get_chat_profile.return_value = profile
#
#             ask_keycite_settings = AskKeyCiteSettings()
#             mock_map_to_ask_keycite_settings.return_value = ask_keycite_settings
#
#             with pytest.raises(MaliciousContentException) as exception:
#                 summarize_service.summarize(user_id=test_user_id, legacy_id=test_legacy_id,
#                                             headnote_id=test_headnote_id,
#                                             answer_solution_profile=SupportedAnswerConfigurations.WL_50SS_LABS_CHAT3,
#                                             citing_case_ids=[],
#                                             conversation_id=test_conversation_id,
#                                             conversation_entry_id=test_conversation_entry_id,
#                                             conversation_action_type=ConversationActionType.RAG,
#                                             auth_token=test_auth_token,
#                                             worker_task=mock_worker_task)
#             assert expected_generate_answer_error == str(exception.value)
#             update_task_status_calls = mock_worker_task.update_task_status_in_progress.mock_calls
#             assert 2 == len(update_task_status_calls)
#             assert call(0, 'Worker started') == update_task_status_calls[0]
#             assert call(100, 'Worker Failed', {'error': expected_generate_answer_error}) == update_task_status_calls[1]
#             mock_conversation_db_v2_instance.update_conversation_entry.assert_called_once_with(
#                 user_id=test_user_id,
#                 conversation_id=test_conversation_id,
#                 conversation_entry_id=test_conversation_entry_id,
#                 attribute_updates={
#                     Constants.CONV_STATUS: RetrieveConversationEntryStatuses.IN_PROGRESS.value,
#                 })
#             mock_conversation_db_v2_instance.write_failure.assert_called_once_with(
#                 user_id=test_user_id,
#                 conversation_id=test_conversation_id,
#                 conversation_entry_id=test_conversation_entry_id,
#                 error_code=105,
#                 error_message=expected_generate_answer_error
#             )
