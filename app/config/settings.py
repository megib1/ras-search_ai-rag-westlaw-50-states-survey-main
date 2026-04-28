import json
import os
from functools import lru_cache
from typing import Optional, List

from configuration_utils.configuration_core import CoreSettings, replace_region_values_in_settings
from configuration_utils.constants import Constants as SessionConstants
from conversation_core.shared.constants import Constants
from conversation_core.shared.models.answer_profile import AnswerProfile
from conversation_core.shared.profile_mapping_util import get_remapped_openai_profile, OverrideProfileMapping
from conversation_core.shared.services.llm_profile_service import LLMProfileEnvironment
from legislation_survey.config import LegislationSurveySettings
from raslogger.logging_factory import LoggingFactory

from services.helm_service import helm_service

logger = LoggingFactory.get_logger(__name__)


class Settings(CoreSettings):
    PROJECT_NAME: str = "Research Application Services (RAS) AI Acceleration"
    GCS_ENVIRONMENT: str
    patch_unittest: bool = False
    CLUSTER_SHORT: str
    SAGEMAKER_EMBEDDING_ENDPOINT: str
    OPEN_SEARCH_ENDPOINT: str
    OPEN_SEARCH_SECRET_ID: str
    OPEN_AI_SECRET: str
    OPEN_AI_MODEL_NAME_4: str
    OPEN_AI_MODEL_NAME_4_DIRECT: str
    OPEN_AI_DEPLOYMENT_NAME_4: str
    OPEN_AI_MODEL_NAME_4_32K: str
    OPEN_AI_MODEL_NAME_4_32K_DIRECT: str
    OPEN_AI_DEPLOYMENT_NAME_4_32K: str
    OPEN_AI_DEPLOYMENT_NAME_4_TURBO: str
    PL_ANSWER_KEY_SECRET_NAME: str
    PL_ANSWER_GCS_URL: str
    COBALT_SEARCH_URL: str
    DISCOVERY_SEARCH_URL: str
    DYNAMO_TABLE_NAME: str
    LOGGER_FIX_LIST: str
    PASSAGE_RANKER_SAGEMAKER_ENDPOINT_NAME: str
    KEYCITE_PASSAGE_RANKER_SAGEMAKER_ENDPOINT_NAME: str
    S3_BUCKET: str
    UDS_ENDPOINT: str
    RAG_SERVICE_TIMEOUT: str
    TEMP_FOLDER: str
    GCS_USER_SECRET: str
    GCS_URL: str
    AWS_SES_SECRET: str
    DEFAULT_PROFILE_MAPPING_SECRET: str
    DISABLE_ALL_PY_WARNINGS: Optional[bool] = True
    LLM_PROXY_ENABLED: Optional[bool] = False
    LLM_PROXY_BASE_URL: Optional[str] = ""
    LLM_PROXY_AZURE_URL_PATH: Optional[str] = ""
    LLM_PROXY_BEDROCK_URL_PATH: Optional[str] = ""
    AI_CONVERSATIONS_URL: str
    CELERY_WORKER_CONCURRENCY: int

@lru_cache()
def get_settings():
    logger.info("current working directory: " + os.getcwd())
    logger.info("getting settings from file: " + ".env." + os.getenv("ENVIRONMENT", "local"))
    settings = Settings()
    # logger.info("settings are: " + json.dumps(settings.dict()))
    updated_settings = replace_region_values_in_settings(settings)
    logger.info("settings are: " + json.dumps(updated_settings.dict()))
    return updated_settings


def get_openai_secret_name_and_url(profile: str) -> OverrideProfileMapping:
    # This is a temporary configuration until ras config comes into place. This allows remapping to test other systems
    # without changing Westlaw since the profile is hard coded.
    return get_remapped_openai_profile(profile, get_settings().DEFAULT_PROFILE_MAPPING_SECRET)


def map_to_ls_settings(
        settings: Settings,
        auth_token: str,
        solution_profile: str,
        ras_profile: str,
        conversation_id: str,
        conversation_entry_id: str,
        answer_profile: AnswerProfile,
        llm_profile_service,
        cobalt_session: Optional[dict] = None,
        tags: Optional[List[str]] = None,
        conversation_type: Optional[str] = Constants.CONV_INITIAL_CONVERSATION_NAME,
        metadata: Optional[dict] = None,
        user_id: Optional[str] = None,
):
    if metadata is None:
        metadata = {}
    ls_settings = LegislationSurveySettings()
    ls_settings.query_min_char_limit = 1
    ls_settings.query_min_valid_tokens = 1
    ls_settings.auth_token = auth_token
    ls_settings.tags = tags
    ls_settings.profile = solution_profile
    ls_settings.conversation_id = conversation_id
    ls_settings.conversation_entry_id = conversation_entry_id
    ls_settings.open_search_settings.SECRET_OPEN_SEARCH = settings.OPEN_SEARCH_SECRET_ID
    ls_settings.open_search_settings.URL_OPEN_SEARCH = settings.OPEN_SEARCH_ENDPOINT
    ls_settings.ras_generic_search_settings.URL = settings.DISCOVERY_SEARCH_URL
    ls_settings.user_id = user_id

    ls_settings.max_allowed_citations_in_answer = getattr(answer_profile, "max_allowed_citations_in_answer", 40)

    ls_settings.gcs_settings.URL_GCS = settings.GCS_URL
    ls_settings.gcs_settings.GCS_CREDENTIALS_SECRET = settings.GCS_USER_SECRET

    ls_settings.cobalt_settings.URL_COBALT = settings.COBALT_SEARCH_URL
    ls_settings.cobalt_settings.COBALT_SESSION = cobalt_session if cobalt_session is not None else {}
    ls_settings.content_selection_settings.endpoint_name = settings.PASSAGE_RANKER_SAGEMAKER_ENDPOINT_NAME
    ls_settings.ann_settings.ENDPOINT_NAME = settings.SAGEMAKER_EMBEDDING_ENDPOINT

    llm_proxy_env: LLMProfileEnvironment = LLMProfileEnvironment[
        (getattr(answer_profile, "llm_proxy_environment", LLMProfileEnvironment.PREPROD.value)).upper()]
    default_headers = {
        Constants.LLM_PROXY_API_KEY: "__none__",
        Constants.LLM_CHAT_PROFILE_NAME_HEADER: ras_profile,
        Constants.LLM_PROXY_AUTHORIZATION_HEADER: auth_token,
        Constants.LLM_CHILD_ENTRY_HEADER: f"conversation_entry_id={conversation_entry_id}",
        Constants.LLM_PARENT_ENTRY_HEADER: f"conversation_id={conversation_id}",
        Constants.LLM_TYPE_HEADER: conversation_type,
        Constants.LLM_MOCK_RESPONSE_HEADER: getattr(answer_profile, "llm_proxy_mock_enabled", False),
        Constants.LLM_MOCK_SLEEP_HEADER: getattr(answer_profile, "llm_proxy_mock_sleep_override", -1),
        Constants.LLM_MOCK_LABEL_HEADER: "legal",
        Constants.GENERIC_USER_ID_HEADER: ls_settings.cobalt_settings.COBALT_SESSION.get(
            SessionConstants.SESSION_USER_GUID) or user_id,
        Constants.GENERIC_SESSION_ID_HEADER: ls_settings.cobalt_settings.COBALT_SESSION.get(
            SessionConstants.SESSION_SESSION_ID),
        Constants.USER_CLASSIFICATION_HEADER: ls_settings.cobalt_settings.COBALT_SESSION.get(
            SessionConstants.SESSION_USER_CLASSIFICATION),
        Constants.USER_SENSITIVITY_HEADER: ls_settings.cobalt_settings.COBALT_SESSION.get(
            SessionConstants.SESSION_USER_SENSITIVITY),
        Constants.PRODUCT_VIEW: ls_settings.cobalt_settings.COBALT_SESSION.get(
            SessionConstants.SESSION_PRODUCT_VIEW),
        Constants.PRODUCT_NAME: ls_settings.cobalt_settings.COBALT_SESSION.get(
            SessionConstants.SESSION_PRODUCT_NAME),
        Constants.BLUE_GREEN_ROUTING_HEADER: "green" if metadata.get(Constants.TASK_MD_ROUTE_TO_GREEN,
                                                                         False) else "blue",
    }

    if helm_service.is_green:
        default_headers[Constants.BLUE_GREEN_ROUTING_HEADER] = "green"

    default_headers = {k: str(v) for k, v in default_headers.items() if v is not None}
    llm_secrets = llm_profile_service.get_subscription_secret(subscription_name="default",
                                                                                     env=settings.ENVIRONMENT)
    azure_llm_url = f"{settings.LLM_PROXY_BASE_URL}{settings.LLM_PROXY_AZURE_URL_PATH}"


    ls_settings.open_ai_settings.MODEL_SETTINGS_32K.API_BASE_URL = azure_llm_url
    #ls_settings.jurisdiction_extractor_open_ai_settings.MODEL_SETTINGS_32K.API_BASE_URL = azure_llm_url
    default_headers_32k = default_headers.copy()
    default_headers_32k[Constants.LLM_PROFILE_KEY_HEADER] = Constants.LLM_PROFILE_KEY_32K
    ls_settings.open_ai_settings.MODEL_SETTINGS_32K.CUSTOM_HEADERS = default_headers_32k
    ls_settings.open_ai_settings.MODEL_SETTINGS_32K.SECRET_AZURE_OPENAI = llm_secrets.get_secret_name(
        llm_proxy_env.value)
    #ls_settings.jurisdiction_extractor_open_ai_settings.MODEL_SETTINGS_32K.CUSTOM_HEADERS = default_headers_32k

    ls_settings.open_ai_settings.MODEL_SETTINGS_128K.API_BASE_URL = azure_llm_url
    #ls_settings.jurisdiction_extractor_open_ai_settings.MODEL_SETTINGS_128K.API_BASE_URL = azure_llm_url
    default_headers_128k = default_headers.copy()
    default_headers_128k[Constants.LLM_PROFILE_KEY_HEADER] = Constants.LLM_PROFILE_KEY_128K
    ls_settings.open_ai_settings.MODEL_SETTINGS_128K.CUSTOM_HEADERS = default_headers_128k
    ls_settings.open_ai_settings.MODEL_SETTINGS_128K.SECRET_AZURE_OPENAI = llm_secrets.get_secret_name(
        llm_proxy_env.value)
    #ls_settings.jurisdiction_extractor_open_ai_settings.MODEL_SETTINGS_128K.CUSTOM_HEADERS = default_headers_128k

    ls_settings.open_ai_settings.MODEL_SETTINGS_4o.API_BASE_URL = azure_llm_url
    #ls_settings.jurisdiction_extractor_open_ai_settings.MODEL_SETTINGS_4o.API_BASE_URL = azure_llm_url
    default_headers_4o = default_headers.copy()
    default_headers_4o[Constants.LLM_PROFILE_KEY_HEADER] = "gpt-4o-2024-11-20"
    ls_settings.open_ai_settings.MODEL_SETTINGS_4o.CUSTOM_HEADERS = default_headers_4o
    ls_settings.open_ai_settings.MODEL_SETTINGS_4o.SECRET_AZURE_OPENAI = llm_secrets.get_secret_name(
        llm_proxy_env.value)
    #ls_settings.jurisdiction_extractor_open_ai_settings.MODEL_SETTINGS_4o.CUSTOM_HEADERS = default_headers_4o

    ls_settings.open_ai_settings.MODEL_SETTINGS_4_1.API_BASE_URL = azure_llm_url
    # ls_settings.jurisdiction_extractor_open_ai_settings.MODEL_SETTINGS_4_1.API_BASE_URL = azure_llm_url
    default_headers_41 = default_headers.copy()
    default_headers_41[Constants.LLM_PROFILE_KEY_HEADER] = "gpt-4.1"
    ls_settings.open_ai_settings.MODEL_SETTINGS_4_1.CUSTOM_HEADERS = default_headers_41
    ls_settings.open_ai_settings.MODEL_SETTINGS_4_1.SECRET_AZURE_OPENAI = llm_secrets.get_secret_name(
       llm_proxy_env.value)

    ls_settings.open_ai_settings.MODEL_SETTINGS_GPT_5_2.API_BASE_URL = azure_llm_url
    # ls_settings.jurisdiction_extractor_open_ai_settings.MODEL_SETTINGS_GPT_5_2.API_BASE_URL = azure_llm_url
    default_headers_52 = default_headers.copy()
    default_headers_52[Constants.LLM_PROFILE_KEY_HEADER] = "gpt-5.2"
    ls_settings.open_ai_settings.MODEL_SETTINGS_GPT_5_2.CUSTOM_HEADERS = default_headers_52
    ls_settings.open_ai_settings.MODEL_SETTINGS_GPT_5_2.SECRET_AZURE_OPENAI = llm_secrets.get_secret_name(
       llm_proxy_env.value)

    string_default_headers = {k: str(v) for k, v in default_headers.items()}
    bedrock_llm_url = f"{settings.LLM_PROXY_BASE_URL}{settings.LLM_PROXY_BEDROCK_URL_PATH}"

    ls_settings.anthropic_settings.MODEL_SETTINGS_BEDROCK_3_5_SONNET.API_BASE_URL = bedrock_llm_url
    default_sonnet_3_5_headers = string_default_headers.copy()
    ls_settings.anthropic_settings.MODEL_SETTINGS_BEDROCK_3_5_SONNET.CUSTOM_HEADERS = default_sonnet_3_5_headers
    ls_settings.anthropic_settings.MODEL_SETTINGS_BEDROCK_3_5_SONNET.CUSTOM_HEADERS[Constants.LLM_PROFILE_KEY_HEADER] = "anthropic.claude-3-5-sonnet-20240620-v1:0"
    ls_settings.anthropic_settings.MODEL_SETTINGS_BEDROCK_3_5_SONNET.SECRET_AZURE_OPENAI = llm_secrets.get_secret_name(
        llm_proxy_env.value)

    return ls_settings
