from unittest.mock import patch, mock_open

import pytest
from conversation_core.shared.models.answer_profile import AnswerProfile

from services.email_service import EmailService

mock_timestamp = 1672531199
mock_destination_url = "http://example.com/survey"
mock_success = True
mock_failure = False
mock_ses_post_secret = "mock_secret"
mock_answer_profile = AnswerProfile()
mock_success_email_content = "Hello, your survey is ready! Visit: ~DESTINATION_URL~ on [~DATE~] at [~TIME~] [~AM~]"
mock_failure_email_content = "Hello, there was an issue with your survey. Please try again later."


@pytest.fixture
def email_service():
    return EmailService(ses_secret=mock_ses_post_secret)


class TestEmailService:

    def test_get_email_subject_success(self, email_service):
        subject = email_service.get_email_subject(mock_success, mock_answer_profile)
        assert subject == "Your AI Jurisdictional Survey is ready"

    def test_get_email_subject_failure(self, email_service):
        subject = email_service.get_email_subject(mock_failure, mock_answer_profile)
        assert subject == "Something went wrong when creating your AI Jurisdictional Survey"

    @patch("builtins.open", new_callable=mock_open, read_data=mock_success_email_content)
    def test_generate_email_body_success(self, mock_file, email_service):
        email_body = email_service.generate_email_body(mock_timestamp, mock_destination_url, mock_success,
                                                       mock_answer_profile)
        assert "Visit: http://example.com/survey" in email_body
        assert "on 12/31" in email_body
        assert "at 11:59 p.m." in email_body

    @patch("builtins.open", new_callable=mock_open, read_data=mock_failure_email_content)
    def test_generate_email_body_failure(self, mock_file, email_service):
        email_body = email_service.generate_email_body(mock_timestamp, mock_destination_url, mock_failure,
                                                       mock_answer_profile)
        assert "there was an issue with your survey" in email_body

    @patch("builtins.open", side_effect=ValueError("Invalid timestamp"))
    def test_generate_email_body_value_error(self, mock_file, email_service):
        email_body = email_service.generate_email_body("invalid_timestamp", mock_destination_url, mock_success,
                                                       mock_answer_profile)
        assert email_body == ""

    @patch("builtins.open", side_effect=Exception("File not found"))
    def test_generate_email_body_generic_exception(self, mock_file, email_service):
        email_body = email_service.generate_email_body(mock_timestamp, mock_destination_url, mock_success,
                                                       mock_answer_profile)
        assert email_body == ""
