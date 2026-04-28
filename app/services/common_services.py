import asyncio
import uuid

from conversation_core.shared.services.profile_service import AnswerProfileService
from legislation_survey.config import LegislationSurveySettings
from conversation_core.shared.services.llm_profile_service import LlmProfileService
from gcs_utils.entitlement_client import EntitlementClient
from raslogger import LoggingFactory

from config.settings import get_settings

logger = LoggingFactory.get_logger(__name__)

_entitlement_client = None
_llm_profile_service = None
settings = get_settings()

def get_entitlement_client(gcs_url: str):
    global _entitlement_client
    if _entitlement_client is None:
        _entitlement_client = EntitlementClient(gcs_entitlement_path=gcs_url)

    return _entitlement_client


def get_llm_profile_service():
    global _llm_profile_service
    if _llm_profile_service is None:
        llm_env = "prod" if settings.ENVIRONMENT == "prod" else "preprod"
        _llm_profile_service = LlmProfileService(ras_config_base_url=settings.RAS_CONFIG_BASE_URL,
                                                 gcs_url=settings.GCS_URL,
                                                 gcs_user_secret=settings.GCS_USER_SECRET,
                                                 llm_environment=llm_env,
                                                 entitlement_client=get_entitlement_client(settings.GCS_URL))
    return _llm_profile_service


def get_or_create_eventloop():
    try:
        loop = asyncio.get_running_loop()
        logger.info(f"Using existing event loop with ID: {id(loop)}")
        return loop
    except RuntimeError as e:
        logger.info(f"Creating new event loop: {e}")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        logger.info(f"Created new event loop with ID: {id(loop)}")
        return loop
    except Exception as e:
        logger.error(f"Error in get_or_create_eventloop: {e}")
        return None


def get_task_id():
    return str(uuid.uuid4())


def log_event_loop_id(task_name):
    try:
        loop = asyncio.get_running_loop()
        logger.info(f"Task '{task_name}' running on event loop with ID: {id(loop)}")
    except Exception as e:
        logger.error(f"Error in log_event_loop_id {task_name}: {e}")

def refresh_auth_token(ls_settings: LegislationSurveySettings, gcs_user_secret: str):
    entitlement_client = get_entitlement_client(gcs_url=settings.GCS_URL)
    updated_auth_token = entitlement_client.get_auth_token(gcs_user_secret).replace("Bearer ", "")
    auth_token = updated_auth_token
    ls_settings.auth_token = auth_token

# initiating the answer profile service with the required parameters
answer_profile_service: AnswerProfileService = AnswerProfileService(gcs_url=settings.GCS_URL,
                                                                    gcs_user_secret=settings.GCS_USER_SECRET,
                                                                    ras_config_base_url=settings.RAS_CONFIG_BASE_URL,
                                                                    entitlement_client = get_entitlement_client(gcs_url=settings.GCS_URL))