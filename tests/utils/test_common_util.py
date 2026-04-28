from unittest.mock import patch, mock_open, MagicMock

from utils.common_util import mock_open_ai_response, mock_additional_content_response, mocked_response


class TestMockOpenAiResponse:
    answer_solution_profile = 'westlaw_50ss_chat_profile3-scale-mock'

    def test_mock_open_ai_response_when_new_conversation(self):
        actual_answer = mock_open_ai_response(self.answer_solution_profile, True)
        assert actual_answer is not None
        assert actual_answer['mock_answer'] is not None
        assert len(actual_answer['mock_answer']) != 0
        assert actual_answer['mock_open_ai']
        assert actual_answer['intent_label'] == 'legal'
        assert actual_answer['sleep_time'] >= 0

    def test_mock_open_ai_response_when_existing_conversation(self):
        actual_answer = mock_open_ai_response(self.answer_solution_profile, False)
        assert actual_answer is not None
        assert actual_answer['mock_answer'] is not None
        assert len(actual_answer['mock_answer']) != 0
        assert actual_answer['mock_open_ai']
        assert actual_answer['intent_label'] == 'legal'
        assert actual_answer['sleep_time'] >= 0

    def test_mock_open_ai_response_with_unknown_profile(self):
        actual_answer = mock_open_ai_response('unknown_profile', True)
        assert actual_answer['mock_answer'] is None
        assert not actual_answer['mock_open_ai']
        assert actual_answer['intent_label'] is None
        assert actual_answer['sleep_time'] == 0.0001

    @patch('builtins.open', new_callable=mock_open,
           read_data='{"westlaw_50ss_chat_profile3-scale-mock": {"mockAnswers": [], "mockOpenAI": true, "intentLabel": "legal", "initialSleepTimeRange": {"min": 1, "max": 2}, "followUpSleepTimeRange": {"min": 3, "max": 4}}}')
    def test_mock_open_ai_response_with_empty_mock_answers(self, mock_file):
        actual_answer = mock_open_ai_response(self.answer_solution_profile, True)
        assert actual_answer['mock_answer'] is None
        assert not actual_answer['mock_open_ai']
        assert actual_answer['intent_label'] is None
        assert actual_answer['sleep_time'] == 0.0001

    @patch('builtins.open', new_callable=mock_open,
           read_data='{"westlaw_50ss_chat_profile3-scale-mock": {"mockAnswers": ["test"], "mockOpenAI": true, "intentLabel": "legal", "initialSleepTimeRange": {"min": 1, "max": 2}, "followUpSleepTimeRange": {"min": 3, "max": 4}}}')
    def test_mock_open_ai_response_sleep_time_ranges(self, mock_file):
        actual_answer_new = mock_open_ai_response(self.answer_solution_profile, True)
        assert 1 <= actual_answer_new['sleep_time'] <= 2

        actual_answer_existing = mock_open_ai_response(self.answer_solution_profile, False)
        assert 3 <= actual_answer_existing['sleep_time'] <= 4

    @patch('builtins.open', lambda: MagicMock(side_effect=FileNotFoundError))
    def test_mock_open_ai_when_mock_data_file_not_found(self):
        actual_answer = mock_open_ai_response(self.answer_solution_profile, False)
        assert actual_answer is not None
        assert actual_answer['mock_answer'] is None
        assert not actual_answer['mock_open_ai']
        assert actual_answer['intent_label'] is None
        assert actual_answer['sleep_time'] == 0.0001

    @patch('builtins.open', lambda: MagicMock(side_effect=Exception))
    def test_mock_open_ai_when_file_read_throws_exception(self):
        actual_answer = mock_open_ai_response(self.answer_solution_profile, False)
        assert actual_answer is not None
        assert actual_answer['mock_answer'] is None
        assert not actual_answer['mock_open_ai']
        assert actual_answer['intent_label'] is None
        assert actual_answer['sleep_time'] == 0.0001


class TestMockAdditionalContentResponse:
    answer_solution_profile = 'westlaw_50ss_chat_profile3-scale-mock'

    @patch('builtins.open', new_callable=mock_open,
           read_data='{"westlaw_50ss_chat_profile3-scale-mock": "test content"}')
    def test_mock_additional_content_response_success(self, mock_file):
        actual_answer = mock_additional_content_response(self.answer_solution_profile)
        assert actual_answer == "test content"

    def test_mock_additional_content_response_unknown_profile(self):
        actual_answer = mock_additional_content_response('unknown_profile')
        assert actual_answer is None

    @patch('builtins.open', lambda: MagicMock(side_effect=FileNotFoundError))
    def test_mock_additional_content_response_file_not_found(self):
        actual_answer = mock_additional_content_response(self.answer_solution_profile)
        assert actual_answer is None

    @patch('builtins.open', lambda: MagicMock(side_effect=Exception))
    def test_mock_additional_content_response_exception(self):
        actual_answer = mock_additional_content_response(self.answer_solution_profile)
        assert actual_answer is None


class TestMockedResponse:
    @patch('builtins.open', new_callable=mock_open, read_data='{"test": "data"}')
    def test_mocked_response_success(self, mock_file):
        actual_answer = mocked_response()
        assert actual_answer == {"test": "data"}

    @patch('builtins.open', lambda: MagicMock(side_effect=FileNotFoundError))
    def test_mocked_response_file_not_found(self):
        actual_answer = mocked_response()
        assert actual_answer == {}

    @patch('builtins.open', lambda: MagicMock(side_effect=Exception))
    def test_mocked_response_exception(self):
        actual_answer = mocked_response()
        assert actual_answer == {}
