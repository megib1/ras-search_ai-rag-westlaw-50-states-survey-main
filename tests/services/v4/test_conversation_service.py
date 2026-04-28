from datetime import datetime
from unittest.mock import patch, MagicMock

import pytest
from legislation_survey.dataclasses import LegislationSurveyServiceOutput, \
    LegislationSurveyServiceInput, LegislationAnswer, LegislationSource, LegislationCite, ScoredPassage
from celery.app.task import Context
from celery.contrib.abortable import AbortableTask
from celery.utils.threads import LocalStack
from conversation_core.shared.enums import ConversationActionType, RetrieveConversationEntryStatuses
from conversation_core.shared.enums import IntentClassification
from conversation_core.shared.models.answer_profile import AnswerProfile, ActionSequence
from conversation_core.shared.models.errors import ErrorModel
from conversation_core.shared.models.v2.conversation_entry import ConversationEntry
from conversation_core.shared.models.v2.conversation import Conversation


test_user_id = "user_id"
test_user_input = "Will this test pass?"
test_answer = "42"
test_conversation_id = "conversation_id"
test_conversation_entry_id = "conversation_entry_id"
test_validation_entry_id = "validation_entry_id"
test_skill_router_entry_id = "skill_router_entry_id"
test_intent_resolver_entry_id = "intent_resolver_entry_id"
test_auth_token = "auth_token"
test_title = "title"
test_guid = "guid"
test_conversation_history = [
    ConversationEntry(conversation_entry_id=test_validation_entry_id,
                      user_input=test_user_input,
                      status=RetrieveConversationEntryStatuses.COMPLETE,
                      conversation_entry_metadata={},
                      conversation_action_type=ConversationActionType.VALIDATION,
                      timestamp=int(datetime.strptime('2021-09-01T00:00:00Z', '%Y-%m-%dT%H:%M:%SZ').timestamp()))
]


def generate_westlaw_generate_answer(ls_result: LegislationSurveyServiceOutput):
    from services.v4.conversation_service import LegislationSurveyGenerateAnswer
    return LegislationSurveyGenerateAnswer(
        ls_result=ls_result
    )

"""
from services.common_services import (get_or_create_eventloop,
                                      get_task_id, log_event_loop_id,
                                      answer_profile_service, get_llm_profile_service,
                                      refresh_auth_token)
"""
class TestConversationService:
    @pytest.fixture()
    @patch("services.common_services.get_llm_profile_service")
    def conversation_service(self, mock_get_llm_profile_service,
                             mock_entitlement_client_instance):
        from services.v4.conversation_service import ConversationService

        return ConversationService(entitlement_client=mock_entitlement_client_instance)

    @pytest.fixture
    def rag_service_output(self):
        return LegislationSurveyServiceOutput(
            user_input=LegislationSurveyServiceInput(question=test_user_input),
            answers=[LegislationAnswer(answer_text=test_answer,
                                       jurisdiction="CA",
                                       sources=[LegislationSource(title=test_title,
                                                                  doc_guid=test_guid,
                                                                  passages=[
                                                                      ScoredPassage(passage_id="passage_id")
                                                                  ],
                                                                  fermi_jurisdictions=["CA"]
                                                                  )
                                                ],
                                       cites=[LegislationCite(
                                           start_offset=0,
                                           end_offset=1,
                                           doc_guid=test_guid)]
                                       )
                     ],
            summary=None
        )

    @pytest.fixture
    def rag_service_output_cases_included(self):
        sample_answer = [LegislationAnswer(answer_text=test_answer,
                                       jurisdiction="CA",
                                       sources=[LegislationSource(title=test_title,
                                                                  doc_guid=test_guid,
                                                                  passages=[
                                                                      ScoredPassage(passage_id="passage_id")
                                                                  ],
                                                                  fermi_jurisdictions=["CA"]
                                                                  )
                                                ],
                                       cites=[LegislationCite(
                                           start_offset=0,
                                           end_offset=1,
                                           doc_guid=test_guid)]
                                       )
                     ]
        return LegislationSurveyServiceOutput(
            user_input=LegislationSurveyServiceInput(question=test_user_input),
            answers=sample_answer,
            case_answers=sample_answer,
            summary=None
        )

    class TestGetErrorDetails:
        @patch("services.v4.conversation_service.get_error_retryable")
        @patch("services.v4.conversation_service.get_error_code")
        @patch("services.v4.conversation_service.get_error_message")
        def test_get_error_details(
                self, mock_get_error_message, mock_get_error_code, mock_get_error_retryable, conversation_service
        ):
            retryable = False
            error_code = 503
            error_message = "An error occurred!"

            mock_get_error_retryable.return_value = retryable
            mock_get_error_code.return_value = error_code
            mock_get_error_message.return_value = error_message

            expected_error_details = ErrorModel()
            expected_error_details.is_retryable = retryable
            expected_error_details.code = error_code
            expected_error_details.message = error_message

            actual_error_details = conversation_service.get_error_details(ex=Exception())

            assert retryable == actual_error_details.is_retryable
            assert error_code == actual_error_details.code
            assert error_message == actual_error_details.message

    class TestGenerateAnswer:
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
                intent_profile="wl-intent-resolver-v005b",
                auto_submit_intent_classifications=[IntentClassification.LEGAL,
                                                    IntentClassification.ILLEGAL_INFORMATION],
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
            answer_profile.additional_content_types = []
            return answer_profile

        @pytest.mark.asyncio
        @patch("time.time", lambda: 0.0)
        @patch("legislation_survey.service.LegislationSurveyService.generate_answer")
        async def test_generate_answer(
            self,
            mock_generate_answer,
            answer_data,
            mock_worker_task,
            mock_conversation_db_v2_instance,
            conversation_service,
            profile,
            rag_service_output,
        ):
            mock_conversation_db_v2_result = Conversation(
                user_id=test_user_id,
                conversation_id=test_conversation_id,
                conversation_metadata=None,
                conversation_entries=test_conversation_history,
            )
            mock_conversation_db_v2_instance.get_conversation.return_value = mock_conversation_db_v2_result

            mock_generate_answer.return_value = rag_service_output
            expected_generate_answer = generate_westlaw_generate_answer(
                ls_result= rag_service_output
            )

            conversation_action_sequence = profile.action_sequence[1]

            actual_answer = await conversation_service.generate_answer(
                user_id=test_user_id,
                user_input=test_user_input,
                conversation_id=test_conversation_id,
                conversation_entry_id=test_conversation_entry_id,
                answer_solution_profile=profile.name,
                answer_profile=profile,
                jurisdictions=[],
                content_types=[],
                content_types_exclude=[],
                conversation_action_type=ConversationActionType.RAG,
                auth_token=test_auth_token,
                worker_task=mock_worker_task,
                task_action_sequence=conversation_action_sequence,
                tags=[],
                conversation_history=[],
                user_session={"sessionId": "test_session_id"},
                meta_data={
                    "rag_version": "0.0.1",
                    "app_version": "0.0.2",
                    "python_version": "3.0.0",
                    "conversation_type": "Initial",
                },
            )

            assert expected_generate_answer == actual_answer

        @pytest.mark.asyncio
        @patch("time.time", lambda: 0.0)
        @patch("legislation_survey.service.LegislationSurveyService.generate_answer")
        async def test_generate_answer_cases_included(
            self,
            mock_generate_answer,
            answer_data,
            mock_worker_task,
            mock_conversation_db_v2_instance,
            conversation_service,
            profile,
            rag_service_output_cases_included,
        ):
            mock_conversation_db_v2_result = Conversation(
                user_id=test_user_id,
                conversation_id=test_conversation_id,
                conversation_metadata=None,
                conversation_entries=test_conversation_history,
            )
            mock_conversation_db_v2_instance.get_conversation.return_value = mock_conversation_db_v2_result

            mock_generate_answer.return_value = rag_service_output_cases_included
            expected_generate_answer = generate_westlaw_generate_answer(
                ls_result=rag_service_output_cases_included
            )

            conversation_action_sequence = profile.action_sequence[1]

            actual_answer = await conversation_service.generate_answer(
                user_id=test_user_id,
                user_input=test_user_input,
                conversation_id=test_conversation_id,
                conversation_entry_id=test_conversation_entry_id,
                answer_solution_profile=profile.name,
                answer_profile=profile,
                jurisdictions=[],
                content_types=[],
                content_types_exclude=[],
                conversation_action_type=ConversationActionType.RAG,
                auth_token=test_auth_token,
                worker_task=mock_worker_task,
                task_action_sequence=conversation_action_sequence,
                tags=[],
                conversation_history=[],
                user_session={"sessionId": "test_session_id"},
                meta_data={
                    "rag_version": "0.0.1",
                    "app_version": "0.0.2",
                    "python_version": "3.0.0",
                    "conversation_type": "Initial",
                },
                additional_user_inputs={"include_cases": True}
            )

            assert expected_generate_answer == actual_answer

