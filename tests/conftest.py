import pytest
import json
import os
from typing import Dict, Any
from unittest.mock import MagicMock, patch

dir_name = os.path.dirname(__file__)

mock_db = MagicMock()
mock_db_v2 = MagicMock()
mock_mail_client = MagicMock()
mock_entitlement_client = MagicMock()
mock_answer_profile_service = MagicMock()


@pytest.fixture
def mock_entitlement_client_instance():
    yield mock_entitlement_client
    mock_entitlement_client.reset_mock(side_effect=True)


@pytest.fixture
def additional_content_data() -> Dict[str, Any]:
    input_file = os.path.join(dir_name, 'data/generated_additional_content.json')
    with (open(input_file, 'r') as input_f):
        input_data: Dict[str, Any] = json.load(input_f)
        return input_data


@pytest.fixture
def additional_content_snippets_data() -> Dict[str, Any]:
    input_file = os.path.join(dir_name, 'data/generated_additional_content_snippets.json')
    with (open(input_file, 'r') as input_f):
        input_data: Dict[str, Any] = json.load(input_f)
        return input_data


@pytest.fixture
def answer_data() -> Dict[str, Any]:
    input_file = os.path.join(dir_name, 'data/generated_answer.json')
    with open(input_file, 'r') as input_f:
        input_data: Dict[str, Any] = json.load(input_f)
        return input_data


@pytest.fixture
def answer_data_cites() -> Dict[str, Any]:
    input_file = os.path.join(dir_name, 'data/generated_answer_cites.json')
    with open(input_file, 'r') as input_f:
        input_data = json.load(input_f)
        return input_data


@pytest.fixture
def answer_data_cites_reranked() -> Dict[str, Any]:
    input_file = os.path.join(dir_name, 'data/generated_answer_cites_reranked.json')
    with open(input_file, 'r') as input_f:
        input_data = json.load(input_f)
        return input_data


@pytest.fixture
def mock_conversation_db_instance():
    yield mock_db
    mock_db.reset_mock(side_effect=True)


@pytest.fixture
def mock_conversation_db_v2_instance():
    yield mock_db_v2
    mock_db_v2.reset_mock(side_effect=True)


@pytest.fixture
def mock_emc_instance():
    yield mock_mail_client
    mock_mail_client.reset_mock(side_effect=True)


@pytest.fixture
def mock_profile_service_instance():
    yield mock_answer_profile_service
    mock_answer_profile_service.reset_mock(side_effect=True)


@pytest.fixture(scope='session', autouse=True)
def global_mocks():
    email_boto3 = patch('conversation_core.shared.services.email_service_base.boto3.client')
    conversation_db_patcher = patch('conversation_core.shared.dynamo_helper.ConversationDB.__new__')
    conversation_db_v2_patcher = patch('conversation_core.shared.dynamo_helper_v2.ConversationDB.__new__')
    profile_service_patcher = patch('conversation_core.shared.services.profile_service.AnswerProfileService.__new__')
    get_openai_secret_name_and_url_patcher = patch('app.config.settings.get_openai_secret_name_and_url')
    entitlement_client_patcher = patch("gcs_utils.entitlement_client.EntitlementClient.__new__")

    mock_mail_client.get_secret_value.return_value = {
        'SecretString': json.dumps({
            'access_key_id': 'someid', 'secret_access_key': 'somesecret'
        })
    }
    mock_email_boto3 = email_boto3.start()
    mock_conversation_db = conversation_db_patcher.start()
    mock_conversation_db_v2 = conversation_db_v2_patcher.start()
    mock_profile_service = profile_service_patcher.start()
    mock_get_openai_secret_name_and_url = get_openai_secret_name_and_url_patcher.start()
    mock_entitle_client = entitlement_client_patcher.start()

    mock_email_boto3.return_value = mock_mail_client
    mock_conversation_db.return_value = mock_db
    mock_conversation_db_v2.return_value = mock_db_v2
    mock_profile_service.return_value = mock_answer_profile_service
    mock_get_openai_secret_name_and_url.return_value = 'mock_openai_secret_value'
    mock_entitle_client.return_value = mock_entitlement_client

    yield

    mock_email_boto3.stop()
    conversation_db_patcher.stop()
    conversation_db_v2_patcher.stop()
    profile_service_patcher.stop()
    get_openai_secret_name_and_url_patcher.stop()
    entitlement_client_patcher.stop()


@pytest.fixture(scope='session')
def celery_includes():
    return ['worker.conversation_tasks']