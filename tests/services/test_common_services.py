from unittest.mock import patch, MagicMock

import pytest


@pytest.fixture(autouse=True)
def reset_globals():
    import services.common_services
    services.common_services._entitlement_client = None
    services.common_services._llm_profile_service = None


@pytest.fixture
def mock_settings():
    settings = MagicMock()
    settings.ENVIRONMENT = "prod"
    settings.RAS_CONFIG_BASE_URL = "https://ras-config.example.com"
    settings.GCS_URL = "https://gcs.example.com"
    settings.GCS_USER_SECRET = "secret"
    return settings


@pytest.fixture()
def fake_get_entitlement_client(mock_settings):
    import services.common_services
    services.common_services.settings = mock_settings
    return services.common_services.get_entitlement_client

@pytest.fixture()
def fake_get_llm_profile_service(mock_settings):
    import services.common_services
    services.common_services.settings = mock_settings
    return services.common_services.get_llm_profile_service


class TestGetEntitlementClient:

    @patch('services.common_services.EntitlementClient')
    def test_get_entitlement_client_success(self, mock_entitlement_client, fake_get_entitlement_client):
        gcs_url = "https://example.com/gcs"
        client = fake_get_entitlement_client(gcs_url)
        mock_entitlement_client.assert_called_once_with(gcs_entitlement_path=gcs_url)
        assert client == mock_entitlement_client.return_value

    @patch('services.common_services.EntitlementClient')
    def test_get_entitlement_client_caching(self, mock_entitlement_client, fake_get_entitlement_client):
        gcs_url = "https://example.com/gcs"
        client1 = fake_get_entitlement_client(gcs_url)
        client2 = fake_get_entitlement_client(gcs_url)
        assert mock_entitlement_client.call_count == 1
        assert client1 == client2

    @patch('services.common_services.EntitlementClient')
    def test_get_entitlement_client_different_urls(self, mock_entitlement_client, fake_get_entitlement_client):
        url1 = "https://example1.com/gcs"
        url2 = "https://example2.com/gcs"
        client1 = fake_get_entitlement_client(url1)
        client2 = fake_get_entitlement_client(url2)
        assert mock_entitlement_client.call_count == 1
        assert client1 == client2


class TestGetLlmProfileService:

    @patch('services.common_services.LlmProfileService')
    @patch('services.common_services.get_entitlement_client')
    def test_get_llm_profile_service_prod(self, mock_get_entitlement_client,
                                          mock_llm_profile_service, mock_settings,
                                          fake_get_llm_profile_service):
        service = fake_get_llm_profile_service()
        mock_get_entitlement_client.assert_called_once_with(mock_settings.GCS_URL)
        mock_llm_profile_service.assert_called_once_with(ras_config_base_url=mock_settings.RAS_CONFIG_BASE_URL,
                                                         gcs_url=mock_settings.GCS_URL,
                                                         gcs_user_secret=mock_settings.GCS_USER_SECRET,
                                                         llm_environment="prod",
                                                         entitlement_client=mock_get_entitlement_client.return_value)
        assert service == mock_llm_profile_service.return_value

    @patch('services.common_services.LlmProfileService')
    @patch('services.common_services.get_entitlement_client')
    def test_get_llm_profile_service_preprod(self, mock_get_entitlement_client, mock_llm_profile_service,
                                             mock_settings,
                                             fake_get_llm_profile_service):
        mock_settings.ENVIRONMENT = "staging"
        service = fake_get_llm_profile_service()
        mock_llm_profile_service.assert_called_once_with(ras_config_base_url=mock_settings.RAS_CONFIG_BASE_URL,
                                                         gcs_url=mock_settings.GCS_URL,
                                                         gcs_user_secret=mock_settings.GCS_USER_SECRET,
                                                         llm_environment="preprod",
                                                         entitlement_client=mock_get_entitlement_client.return_value)

    @patch('services.common_services.LlmProfileService')
    @patch('services.common_services.get_entitlement_client')
    def test_get_llm_profile_service_caching(self, mock_get_entitlement_client,
                                             mock_llm_profile_service,
                                             mock_settings,
                                             fake_get_llm_profile_service
                                             ):
        service1 = fake_get_llm_profile_service()
        service2 = fake_get_llm_profile_service()
        assert mock_llm_profile_service.call_count == 1
        assert service1 == service2

    @patch('services.common_services.LlmProfileService')
    @patch('services.common_services.get_entitlement_client')
    def test_get_llm_profile_service_different_settings(self, mock_get_entitlement_client,
                                                        mock_llm_profile_service,
                                                        mock_settings,
                                                        fake_get_llm_profile_service):
        service1 = fake_get_llm_profile_service()
        mock_settings.ENVIRONMENT = "staging"
        service2 = fake_get_llm_profile_service()
        assert mock_llm_profile_service.call_count == 1
        assert service1 == service2