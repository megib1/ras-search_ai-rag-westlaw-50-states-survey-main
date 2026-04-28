from legislation_survey.errors import *
from utils.custom_exceptions import *


class ExceptionMapping:
    def __init__(self, error_code: int = 500, error_message: str = None, retryable: bool = True):
        self.error_code = error_code
        self.error_message = error_message
        self.retryable = retryable


error_dict = {
    MaliciousContentException: ExceptionMapping(error_code=105, retryable=False),
    ConfigError: ExceptionMapping(error_code=200),
    CobaltSearchError: ExceptionMapping(error_code=200),
    OpenSearchError: ExceptionMapping(error_code=200),
    IntentClassifierError: ExceptionMapping(error_code=200),
    PreProcessingError: ExceptionMapping(error_code=200),
    PostProcessingError: ExceptionMapping(error_code=200),
    LLMError: ExceptionMapping(error_code=200),
    AuthenticationError: ExceptionMapping(error_code=200),
    NoMetadataError: ExceptionMapping(error_code=200),
    NoPassagesError: ExceptionMapping(error_code=200),
    SagemakerError: ExceptionMapping(error_code=200),
    AnsValidationError: ExceptionMapping(error_code=200)
}


def get_exception_mapping(exception) -> ExceptionMapping:
    exception_mapping = error_dict.get(type(exception))
    if exception_mapping is not None:
        return exception_mapping
    else:
        return ExceptionMapping(error_code=500,
                                error_message="There was an error processing your request. Please try again later.",
                                retryable=True)


def get_error_code(exception) -> int:
    return get_exception_mapping(exception).error_code


def get_error_message(exception) -> str:
    error_message = get_exception_mapping(exception).error_message
    if error_message is not None:
        return error_message
    else:
        return str(exception)


def get_error_retryable(exception) -> bool:
    return get_exception_mapping(exception).retryable
