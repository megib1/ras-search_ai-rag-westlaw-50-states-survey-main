import json
import random
from pathlib import Path
from raslogger import LoggingFactory

logger = LoggingFactory.get_logger(__name__)


def mock_open_ai_response(answer_solution_profile, is_new_conversation):
    mock_open_ai = False
    mock_answer = None
    sleep_time = 0.0001
    intent_label = None
    try:
        with open(Path('app/resources/open_ai_mock_responses.json').absolute(), 'r') as file:
            parsed_data = json.load(file)

        answer_profile = answer_solution_profile.lower()
        if answer_profile in parsed_data:
            values = parsed_data[answer_profile]
            mock_answer = random.choice(values.get('mockAnswers', []))
            mock_open_ai = values.get('mockOpenAI', False)
            intent_label = values.get('intentLabel', "legal")
            if is_new_conversation:
                min_val = values.get('initialSleepTimeRange').get('min')
                max_val = values.get('initialSleepTimeRange').get('max')
            else:
                min_val = values.get('followUpSleepTimeRange').get('min')
                max_val = values.get('followUpSleepTimeRange').get('max')
            sleep_time = random.randint(min_val, max_val)
    except FileNotFoundError:
        logger.error(
            f"{mock_open_ai_response.__name__}:: file not "
            f"found")
    except Exception as e:
        logger.error(
            f"{mock_open_ai_response.__name__}:: exception "
            f"occurred {e} ")
    return {'mock_open_ai': mock_open_ai, 'mock_answer': mock_answer, 'sleep_time': sleep_time,
            'intent_label': intent_label}


def mock_additional_content_response(answer_solution_profile):
    try:
        with open(Path('app/resources/additional_supporting_material_responses.json').absolute(), 'r') as file:
            parsed_data = json.load(file)
        answer_profile = answer_solution_profile.lower()
        if answer_profile in parsed_data:
            return parsed_data[answer_profile]
    except FileNotFoundError:
        logger.error(
            f"{mock_additional_content_response.__name__}:: file not "
            f"found ")
    except Exception as e:
        logger.error(
            f"{mock_additional_content_response.__name__}:: exception "
            f"occurred {e} ")
    return None


# Temporary method, remove it once labs wheel is ready with new pipeline
def mocked_response():
    parsed_data = {}
    try:
        with open(Path('app/resources/mocked_response.json').absolute(), 'r') as file:
            parsed_data = json.load(file)
    except FileNotFoundError:
        logger.error(
            f"{mocked_response.__name__}:: file not "
            f"found")
    except Exception as e:
        logger.error(
            f"{mocked_response.__name__}:: exception "
            f"occurred {e} ")
    return parsed_data
