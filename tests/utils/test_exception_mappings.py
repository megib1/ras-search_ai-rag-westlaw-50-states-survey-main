import pytest
from legislation_survey.errors import *
from utils.custom_exceptions import *
from utils.exception_mappings import ExceptionMapping, get_exception_mapping, get_error_code, get_error_message, \
    get_error_retryable


class TestExceptionHandling:

    def test_exception_mapping_initialization(self):
        mapping = ExceptionMapping(error_code=400, error_message="Bad Request", retryable=False)
        assert mapping.error_code == 400
        assert mapping.error_message == "Bad Request"
        assert mapping.retryable == False

    def test_get_exception_mapping_known_exception(self):
        exception = MaliciousContentException()
        mapping = get_exception_mapping(exception)
        assert isinstance(mapping, ExceptionMapping)
        assert mapping.error_code == 105
        assert mapping.retryable == False

    def test_get_exception_mapping_unknown_exception(self):
        class UnknownException(Exception):
            pass

        exception = UnknownException()
        mapping = get_exception_mapping(exception)
        assert isinstance(mapping, ExceptionMapping)
        assert mapping.error_code == 500
        assert mapping.error_message == "There was an error processing your request. Please try again later."
        assert mapping.retryable == True

    def test_get_error_code(self):
        assert get_error_code(MaliciousContentException()) == 105
        assert get_error_code(ConfigError()) == 200
        assert get_error_code(Exception()) == 500

    def test_get_error_message(self):
        assert get_error_message(MaliciousContentException()) == str(MaliciousContentException())

        class CustomException(Exception):
            def __init__(self):
                super().__init__("There was an error processing your request. Please try again later.")

        assert get_error_message(
            CustomException()) == "There was an error processing your request. Please try again later."

    def test_get_error_retryable(self):
        assert not get_error_retryable(MaliciousContentException())
        assert get_error_retryable(ConfigError())
        assert get_error_retryable(Exception())

    @pytest.mark.parametrize("exception_class, expected_code",
                             [(ConfigError, 200), (CobaltSearchError, 200), (OpenSearchError, 200),
                              (IntentClassifierError, 200), (PreProcessingError, 200), (PostProcessingError, 200),
                              (LLMError, 200), (AuthenticationError, 200), (NoMetadataError, 200),
                              (NoPassagesError, 200), (SagemakerError, 200), (AnsValidationError, 200), ])
    def test_error_codes(self, exception_class, expected_code):
        assert get_error_code(exception_class()) == expected_code
