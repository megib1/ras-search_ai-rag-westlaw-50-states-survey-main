from unittest import mock

import pytest
from conversation_core.shared.constants import AnnotationType
from conversation_core.shared.models.answer_profile import AnswerProfile


class TestIsValidationSufficientToSubmit:
    @pytest.mark.parametrize(
        ("response", "expected"),
        [
            pytest.param(
                {"system_output": {"annotations": [{"type": AnnotationType.ADVERSARIAL, "value": True}]}},
                False,
                id="adversarial_true_returns_false",
            ),
            pytest.param(
                {"system_output": {"annotations": [{"type": AnnotationType.QUERY_VALIDATION_ERROR, "value": False}]}},
                False,
                id="query_validation_error_always_returns_false",
            ),
            pytest.param(
                {"system_output": {"annotations": [{"type": AnnotationType.ADVERSARIAL, "value": False}]}},
                True,
                id="non_blocking_annotation_returns_true",
            ),
            pytest.param(
                {"other_key": "value"},
                False,
                id="no_system_output_returns_false",
            ),
        ],
    )
    def test_annotation_logic(self, response, expected):
        from services.validation_service import is_validation_sufficient_to_submit

        result = is_validation_sufficient_to_submit(response)
        assert result is expected


class TestValidationService:
    @pytest.fixture
    def service(self):
        from services.validation_service import ValidationService

        return ValidationService()

    @mock.patch("requests.post")
    def test_do_validation_calls_request_evaluator_and_returns_json(self, mock_post, service):
        mock_response = mock.MagicMock()
        mock_response.json.return_value = {"system_output": {"annotations": []}}
        mock_post.return_value = mock_response

        result = service.do_validation(
            user_input="test query",
            answer_solution_profile="wl-rag-v054",
            auth_token="token",
            pipeline_name="wl-common-ir-validate-v001",
            user_session={},
        )

        assert result == {"system_output": {"annotations": []}}
        mock_post.assert_called_once()

    def test_handle_error_does_not_raise(self, service):
        service.handle_error(
            user_id="user-1",
            conversation_id="conv-1",
            conversation_entry_id="entry-1",
            answer_profile=mock.MagicMock(spec=AnswerProfile),
            meta_data={},
            ex=Exception("test"),
        )
