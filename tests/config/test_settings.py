from unittest import mock

import pytest

import config.settings as settings_module
from config.settings import get_settings, map_to_ls_settings
from conversation_core.shared.constants import Constants
from conversation_core.shared.services import llm_profile_service

USER_ID_HEADER = Constants.GENERIC_USER_ID_HEADER  # "x-tr-userid"

SESSION_WITH_USER_GUID = {"userGuid": "session-user-123"}
SESSION_WITHOUT_USER_GUID = {"productName": "Westlaw"}


@pytest.fixture(autouse=True)
def mock_llm_profile_service(monkeypatch):
    mock_service = mock.MagicMock()
    mock_service.return_value.get_subscription_secret.return_value.get_secret_name.return_value = "secret"
    monkeypatch.setattr(llm_profile_service, "LlmProfileService", mock_service)


def _call_map_to_ls_settings(cobalt_session=None, user_id=None):
    from services.common_services import get_llm_profile_service

    return map_to_ls_settings(
        settings=get_settings(),
        auth_token="token",
        solution_profile="profile",
        ras_profile="ras_profile",
        conversation_id="conv-id",
        conversation_entry_id="entry-id",
        answer_profile=mock.MagicMock(llm_proxy_environment="preprod"),
        llm_profile_service=get_llm_profile_service(),
        cobalt_session=cobalt_session,
        user_id=user_id,
    )


@pytest.fixture(autouse=True)
def _patch_helm_service(monkeypatch):
    mock_helm = mock.MagicMock()
    mock_helm.is_green = False

    monkeypatch.setattr(settings_module, "helm_service", mock_helm)


class TestMapToLsSettingsUserIdHeader:
    def test_session_user_guid_populates_header(self):
        result = _call_map_to_ls_settings(cobalt_session=SESSION_WITH_USER_GUID)

        assert result.open_ai_settings.MODEL_SETTINGS_32K.CUSTOM_HEADERS[USER_ID_HEADER] == "session-user-123"
        assert result.open_ai_settings.MODEL_SETTINGS_128K.CUSTOM_HEADERS[USER_ID_HEADER] == "session-user-123"
        assert result.open_ai_settings.MODEL_SETTINGS_4o.CUSTOM_HEADERS[USER_ID_HEADER] == "session-user-123"
        assert result.open_ai_settings.MODEL_SETTINGS_4_1.CUSTOM_HEADERS[USER_ID_HEADER] == "session-user-123"

    def test_user_id_fallback_used_when_session_has_no_guid(self):
        result = _call_map_to_ls_settings(cobalt_session=SESSION_WITHOUT_USER_GUID, user_id="fallback-user-456")

        assert result.open_ai_settings.MODEL_SETTINGS_32K.CUSTOM_HEADERS[USER_ID_HEADER] == "fallback-user-456"
        assert result.open_ai_settings.MODEL_SETTINGS_128K.CUSTOM_HEADERS[USER_ID_HEADER] == "fallback-user-456"
        assert result.open_ai_settings.MODEL_SETTINGS_4o.CUSTOM_HEADERS[USER_ID_HEADER] == "fallback-user-456"
        assert result.open_ai_settings.MODEL_SETTINGS_4_1.CUSTOM_HEADERS[USER_ID_HEADER] == "fallback-user-456"

    def test_user_id_fallback_used_when_cobalt_session_is_none(self):
        result = _call_map_to_ls_settings(cobalt_session=None, user_id="fallback-user-789")

        assert result.open_ai_settings.MODEL_SETTINGS_32K.CUSTOM_HEADERS[USER_ID_HEADER] == "fallback-user-789"

    def test_session_guid_takes_priority_over_user_id_fallback(self):
        result = _call_map_to_ls_settings(cobalt_session=SESSION_WITH_USER_GUID, user_id="fallback-user-456")

        assert result.open_ai_settings.MODEL_SETTINGS_32K.CUSTOM_HEADERS[USER_ID_HEADER] == "session-user-123", (
            "Session userGuid must take priority over user_id fallback"
        )

    def test_header_absent_when_neither_session_guid_nor_user_id_provided(self):
        result = _call_map_to_ls_settings(cobalt_session=SESSION_WITHOUT_USER_GUID, user_id=None)

        assert USER_ID_HEADER not in result.open_ai_settings.MODEL_SETTINGS_32K.CUSTOM_HEADERS, (
            "x-tr-userid must be dropped when no user identity is available"
        )
        assert USER_ID_HEADER not in result.open_ai_settings.MODEL_SETTINGS_128K.CUSTOM_HEADERS
        assert USER_ID_HEADER not in result.open_ai_settings.MODEL_SETTINGS_4o.CUSTOM_HEADERS
        assert USER_ID_HEADER not in result.open_ai_settings.MODEL_SETTINGS_4_1.CUSTOM_HEADERS
