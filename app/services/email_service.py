from datetime import datetime as dt

from conversation_core.shared.services.email_service_base import EmailServiceSESBase
from conversation_core.shared.models.answer_profile import AnswerProfile
from pathlib import Path
from raslogger import LoggingFactory

logger = LoggingFactory.get_logger(__name__)


class EmailService(EmailServiceSESBase):
    def __init__(self, ses_secret: str):
        super().__init__(ses_secret=ses_secret)

    def get_email_subject(self, success: bool, answer_profile: AnswerProfile) -> str:
        return (
            "Your AI Jurisdictional Survey is ready"
            if success
            else "Something went wrong when creating your AI Jurisdictional Survey"
        )

    def generate_email_body(
        self, timestamp: int, destination_url: str, success: bool, answer_profile: AnswerProfile
    ) -> str:
        try:
            filename = "app/resources/email_success.html" if success else "app/resources/email_failure.html"
            with open(Path(filename).absolute(), "r") as email_content:
                email_body = email_content.read()
            datetime_obj = dt.fromtimestamp(timestamp)
            formatted_datetime = datetime_obj.strftime("%m/%d %I:%M %p").replace("PM", "p.m.").replace("AM", "a.m.")
            date_part, time_part, am_pm = formatted_datetime.split(" ")
            replacements = {
                "~DESTINATION_URL~": destination_url,
                "[~DATE~]": date_part,
                "[~TIME~]": time_part,
                "[~AM~]": am_pm,
            }
            for placeholder, value in replacements.items():
                email_body = email_body.replace(placeholder, value)
        except ValueError as ve:
            logger.error("Error formatting timestamp to datetime: {}".format(ve))
            return ""
        except Exception as ex:
            logger.error("An exception occurred while generating email body: {}".format(ex))
            return ""

        return email_body
