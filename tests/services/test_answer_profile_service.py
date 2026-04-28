from unittest.mock import MagicMock

import pytest
from conversation_core.shared.services.profile_service import AnswerProfileService


class TestAnswerProfileService:
    @pytest.fixture
    def answer_profile_service(self):
        gcs_url = 'mock_gcs_url'
        gcs_user_secret = 'mock_gcs_user_secret'
        ras_config_base_url = 'mock_ras_config_base_url'
        entitlement_client = MagicMock()
        return AnswerProfileService(gcs_url=gcs_url, gcs_user_secret=gcs_user_secret,
                                    ras_config_base_url=ras_config_base_url, entitlement_client=entitlement_client)

    def test_answer_profile_service(self, answer_profile_service):
        arg = 'test_arg'
        expected_result = 'expected_result'
        answer_profile_service.some_method = MagicMock(return_value=expected_result)
        result = answer_profile_service.some_method(arg)
        assert result == expected_result
        answer_profile_service.some_method.assert_called_once_with(arg)