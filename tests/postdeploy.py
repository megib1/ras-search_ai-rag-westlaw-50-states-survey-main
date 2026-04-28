from ras_qa_testing import EventFactory, TestFactory

'''
This file is meant to represent the file that calls the tests within the microservice
'''

def get_worker_tests():
    # Payload for initial conversation
    base_payload = {
        "user_input": "Can an owner of a vehicle testify to its loss of value due to the fact the vehicle was in a wreck, damaged, and repaired, even though the owner is not an expert?",
        "answer_solution_profile": "westlaw_AIJS_50states_survey_postdeploy",
        "subscribed_skills": [],
        "additional_user_inputs": {
            "include_cases": "true"
            ,"include_related_federal": "true"
        },
        "overrides": {
            "jurisdictions": [
                "CA-CS",
                "TX-CS",
                "IN-CS",
                "IL-CS",
                "NJ-CS",
                "WA-CS",
                "PA-CS",
                "LA-CS",
                "NV-CS",
                "AL-CS"
            ]
        }
    }
    custom_header = {
            "x-tr-userid": "postdeploy-user",
            "x-tr-sessionid": "postdeploy-session",
            "x-tr-asset-id": "123456"
        }
    initial_conversation_validations = EventFactory.create_event(
        name="start_conversation",
        payload=base_payload,
        response_validation_schema={},
        output_validation=[
            EventFactory.initialize_output_validation(
                validation_type="exists",
                composite_key=["conversation_id"],
                expected_value=""
            ),
            EventFactory.initialize_output_validation(
                validation_type="explicit",
                composite_key=["conversation_metadata", "current_action_sequence_task", "action_type"],
                expected_value="rag"
            ),
            EventFactory.initialize_output_validation(
                composite_key=["conversation_entries", 0, "result", "system_output"],
                validation_type="exists",
                expected_value=""
            ),
            EventFactory.initialize_output_validation(
                composite_key=["conversation_entries", 0, "result", "system_output", "user_input", "question"],
                validation_type="explicit",
                expected_value="Can an owner of a vehicle testify to its loss of value due to the fact the vehicle was in a wreck, damaged, and repaired, even though the owner is not an expert?"
            ),
            EventFactory.initialize_output_validation(
                composite_key=["conversation_metadata", "current_action_sequence_task", "action_status"],
                validation_type="explicit",
                expected_value="Complete"
            ),
            EventFactory.initialize_output_validation(
                composite_key=["conversation_entries", 0, "result", "system_output", "answers"],
                additional_composite_key=["jurisdiction"],
                validation_type="list_values_exists",
                expected_value=""
            ),
            EventFactory.initialize_output_validation(
                composite_key=["conversation_entries", 0, "result", "system_output", "answers"],
                additional_composite_key=["answer_text"],
                validation_type="list_values_exists",
                expected_value=""
            ),
            EventFactory.initialize_output_validation(
                composite_key=["conversation_entries", 0, "result", "system_output", "case_answers"],
                additional_composite_key=["jurisdiction"],
                validation_type="list_values_exists",
                expected_value=""
            ),
            EventFactory.initialize_output_validation(
                composite_key=["conversation_entries", 0, "result", "system_output", "case_answers"],
                additional_composite_key=["answer_text"],
                validation_type="list_values_exists",
                expected_value=""
            ),EventFactory.initialize_output_validation(
                composite_key=["conversation_entries", 0, "result", "system_output", "federal_case_answers"],
                additional_composite_key=["jurisdiction"],
                validation_type="list_values_exists",
                expected_value=""
            ),
            EventFactory.initialize_output_validation(
                composite_key=["conversation_entries", 0, "result", "system_output", "federal_case_answers"],
                additional_composite_key=["answer_text"],
                validation_type="list_values_exists",
                expected_value=""
            ),
        EventFactory.initialize_output_validation(
            composite_key=["conversation_entries", 0, "result", "system_output", "disclaimer"],
            validation_type="exists",
            expected_value=""
        )
        ],
        request_wait_time=600,
    )

    aijs_test = TestFactory.create_conversations_test(
        test_name="aijs_create_conversation_test",
        api_version='v3',
        events=[initial_conversation_validations],
        custom_content_type='',
        expected_status_code=200,
        header=custom_header,
    )



    tests = [aijs_test]
    return tests


TESTS = get_worker_tests()
