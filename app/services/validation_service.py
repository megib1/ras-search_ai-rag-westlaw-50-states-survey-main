from typing import Any

import requests
from configuration_utils.constants import Constants as ConfigConstants
from conversation_core.shared.constants import AnnotationType
from conversation_core.shared.models.answer_profile import AnswerProfile
from raslogger import LoggingFactory
from requests import Response

from config.settings import get_settings

logger = LoggingFactory.get_logger(__name__)
settings = get_settings()


def is_validation_sufficient_to_submit(validation_response: Any) -> bool:
    if "system_output" in validation_response:
        if "annotations" in validation_response["system_output"]:
            for annotation in validation_response["system_output"]["annotations"]:
                if annotation["type"] == AnnotationType.ADVERSARIAL and annotation["value"]:
                    return False
                if annotation["type"] == AnnotationType.QUERY_VALIDATION_ERROR:
                    return False
            return True
    logger.warning("Could not parse annotations from validation response:\n" + str(validation_response))
    return False


class ValidationService:

    def do_validation(self,
                      user_input: str,
                      answer_solution_profile: str,
                      auth_token: str,
                      pipeline_name: str,
                      user_session: dict = None,
                      ) -> Any:
        response = self.call_request_evaluator(auth_token=auth_token,
                                               user_session=user_session,
                                               user_input=user_input,
                                               answer_solution_profile=answer_solution_profile,
                                               pipeline_name=pipeline_name)
        return response.json()

    @staticmethod
    def call_request_evaluator(auth_token: str, user_session: dict, user_input: str, answer_solution_profile: str,
                               pipeline_name: str) -> Response:
        validation_url = f"{settings.AI_CONVERSATIONS_URL}/api/v1/common/input-validation"
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
            # "x-tr-product-name": user_session.get(ConfigConstants.SESSION_PRODUCT_NAME, "unknown"),
            # "x-tr-product-view": user_session.get(ConfigConstants.SESSION_PRODUCT_VIEW, "unknown"),
        }
        body = {
            "user_input": user_input,
            "answer_solution_profile": answer_solution_profile,
            "pipeline_name": pipeline_name
        }
        response = requests.post(validation_url, json=body, headers=headers)
        return response

    def handle_error(
            self,
            user_id: str,
            conversation_id: str,
            conversation_entry_id: str,
            answer_profile: AnswerProfile,
            meta_data: dict,
            ex: Exception,
    ):
        # TODO: Implement this
        pass