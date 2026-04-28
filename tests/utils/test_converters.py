from unittest import mock

import pytest
from conversation_core.shared.enums import RetrieveConversationEntryStatuses, ConversationActionType
from legislation_survey.dataclasses import (
    LegislationSurveyServiceInput,
    LegislationSurveyServiceOutput,
    LegislationAnswer,
    Summary,
    LegislationCite,
    LegislationSource,
)

from models.legislation_survey_result import LegislationSurveyResult


def _make_legislation_output(
    question: str = "test question",
    answer_text: str = "answer",
    jurisdiction: str = "TX",
) -> LegislationSurveyServiceOutput:
    user_input = LegislationSurveyServiceInput(question=question)
    summary = Summary(summary_text="summary", cites=[])
    cite = LegislationCite(start_offset=0, end_offset=5, doc_guid="doc-1")
    source = LegislationSource(
        doc_guid="src-1",
        fermi_jurisdictions=["TX"],
        title="Test Source",
    )
    answer = LegislationAnswer(
        jurisdiction=jurisdiction,
        answer_text=answer_text,
        sources=[source],
        cites=[cite],
        content_type=None,
    )
    return LegislationSurveyServiceOutput(user_input=user_input, summary=summary, answers=[answer])


def _make_entry(
    status: RetrieveConversationEntryStatuses,
    action_type: ConversationActionType,
    system_output: dict | None = None,
    intermediate_results: dict | None = None,
    timestamp: int = 1,
):
    result = mock.MagicMock()
    result.conversation_action_type = action_type
    result.system_output = system_output
    result.intermediate_results = intermediate_results

    entry = mock.MagicMock()
    entry.status = status.value
    entry.result = result
    entry.timestamp = timestamp
    return entry


class TestConvertLsLabsOutputToLsSurveyResult:
    def test_converts_full_output(self):
        labs_output = _make_legislation_output()

        result = _call_convert(labs_output)

        assert isinstance(result, LegislationSurveyResult)
        assert result.summary.summary_text == "summary"
        assert len(result.answers) == 1
        assert result.answers[0].jurisdiction == "TX"
        assert result.answers[0].answer_text == "answer"
        assert len(result.answers[0].sources) == 1
        assert len(result.answers[0].cites) == 1

    def test_empty_cites_and_sources(self):
        user_input = LegislationSurveyServiceInput(question="q")
        summary = Summary(summary_text="s", cites=[])
        answer = LegislationAnswer(jurisdiction="CA", answer_text="a", sources=[], cites=[], content_type=None)
        labs_output = LegislationSurveyServiceOutput(user_input=user_input, summary=summary, answers=[answer])

        result = _call_convert(labs_output)

        assert len(result.answers[0].sources) == 0
        assert len(result.answers[0].cites) == 0


def _call_convert(labs_output):
    from utils.converters import convert_ls_labs_output_to_ls_survey_result

    return convert_ls_labs_output_to_ls_survey_result(labs_output)


class TestConvertConvEntriesToAalpConvHistory:
    def test_empty_entries_returns_empty(self):
        from utils.converters import convert_conv_entries_to_aalp_conv_history

        result = convert_conv_entries_to_aalp_conv_history([])
        assert result == []

    def test_rag_entry_with_rag_model_appended(self):
        from utils.converters import convert_conv_entries_to_aalp_conv_history

        rag_output = {
            "rag_pipeline_output": {
                "intent": {"user_input": {"content_types": ["STATUTE"]}},
                "user_input": {"content_types": []},
            }
        }
        entry = _make_entry(
            status=RetrieveConversationEntryStatuses.COMPLETE,
            action_type=ConversationActionType.RAG,
            system_output=rag_output,
        )

        result = convert_conv_entries_to_aalp_conv_history([entry], rag_model="RagServiceOutput")

        assert len(result) == 1
        assert result[0]["type"] == "RagServiceOutput"
        assert result[0]["data"]["user_input"]["content_types"] == ["STATUTE"]

    def test_rag_entry_without_rag_model_uses_intermediate_results(self):
        from utils.converters import convert_conv_entries_to_aalp_conv_history

        intermediate = {"some": "data"}
        entry = _make_entry(
            status=RetrieveConversationEntryStatuses.COMPLETE,
            action_type=ConversationActionType.RAG,
            intermediate_results=intermediate,
        )

        result = convert_conv_entries_to_aalp_conv_history([entry], rag_model=None)

        assert result == [intermediate]

    def test_rag_entry_without_rag_model_and_no_intermediate_results_skipped(self):
        from utils.converters import convert_conv_entries_to_aalp_conv_history

        entry = _make_entry(
            status=RetrieveConversationEntryStatuses.COMPLETE,
            action_type=ConversationActionType.RAG,
            intermediate_results=None,
        )

        result = convert_conv_entries_to_aalp_conv_history([entry], rag_model=None)

        assert result == []

    def test_rag_entry_with_rag_model_but_no_rag_pipeline_output_skipped(self):
        from utils.converters import convert_conv_entries_to_aalp_conv_history

        entry = _make_entry(
            status=RetrieveConversationEntryStatuses.COMPLETE,
            action_type=ConversationActionType.RAG,
            system_output={"other_key": "value"},
        )

        result = convert_conv_entries_to_aalp_conv_history([entry], rag_model="RagServiceOutput")

        assert result == []

    def test_intent_entry_with_intent_model_appended(self):
        from utils.converters import convert_conv_entries_to_aalp_conv_history

        intent_output = {"intent": "legal"}
        entry = _make_entry(
            status=RetrieveConversationEntryStatuses.COMPLETE,
            action_type=ConversationActionType.INTENT,
            system_output=intent_output,
        )

        result = convert_conv_entries_to_aalp_conv_history([entry], intent_model="IntentModel")

        assert len(result) == 1
        assert result[0]["type"] == "IntentModel"
        assert result[0]["data"] == intent_output

    def test_intent_entry_with_intent_model_but_no_system_output_skipped(self):
        from utils.converters import convert_conv_entries_to_aalp_conv_history

        entry = _make_entry(
            status=RetrieveConversationEntryStatuses.COMPLETE,
            action_type=ConversationActionType.INTENT,
            system_output=None,
        )

        result = convert_conv_entries_to_aalp_conv_history([entry], intent_model="IntentModel")

        assert result == []

    def test_non_complete_entries_are_skipped(self):
        from utils.converters import convert_conv_entries_to_aalp_conv_history

        entry = _make_entry(
            status=RetrieveConversationEntryStatuses.FAILED,
            action_type=ConversationActionType.RAG,
            system_output={"rag_pipeline_output": {}},
        )

        result = convert_conv_entries_to_aalp_conv_history([entry], rag_model="RagServiceOutput")

        assert result == []

    def test_entries_sorted_by_timestamp(self):
        from utils.converters import convert_conv_entries_to_aalp_conv_history

        intermediate_a = {"order": "a"}
        intermediate_b = {"order": "b"}
        entry_later = _make_entry(
            status=RetrieveConversationEntryStatuses.COMPLETE,
            action_type=ConversationActionType.RAG,
            intermediate_results=intermediate_a,
            timestamp=2,
        )
        entry_earlier = _make_entry(
            status=RetrieveConversationEntryStatuses.COMPLETE,
            action_type=ConversationActionType.RAG,
            intermediate_results=intermediate_b,
            timestamp=1,
        )

        result = convert_conv_entries_to_aalp_conv_history(
            [entry_later, entry_earlier], rag_model=None
        )

        assert result[0] == intermediate_b
        assert result[1] == intermediate_a


class TestConvertConversationEntriesToConversationEntries:
    def test_empty_entries_returns_empty(self):
        from utils.converters import convert_conversation_entries_to_conversation_entries

        result = convert_conversation_entries_to_conversation_entries([])
        assert result == []

    def test_rag_entry_with_rag_model_appended(self):
        from utils.converters import convert_conversation_entries_to_conversation_entries

        rag_output = {
            "rag_pipeline_output": {
                "intent": {"user_input": {"content_types": ["STATUTE"]}},
                "user_input": {"content_types": []},
            }
        }
        entry = _make_entry(
            status=RetrieveConversationEntryStatuses.COMPLETE,
            action_type=ConversationActionType.RAG,
            system_output=rag_output,
        )

        result = convert_conversation_entries_to_conversation_entries([entry], rag_model="RagServiceOutput")

        assert len(result) == 1
        assert result[0]["type"] == "RagServiceOutput"
        assert result[0]["data"]["user_input"]["content_types"] == ["STATUTE"]

    def test_rag_entry_without_rag_model_uses_intermediate_results(self):
        from utils.converters import convert_conversation_entries_to_conversation_entries

        intermediate = {"some": "data"}
        entry = _make_entry(
            status=RetrieveConversationEntryStatuses.COMPLETE,
            action_type=ConversationActionType.RAG,
            intermediate_results=intermediate,
        )

        result = convert_conversation_entries_to_conversation_entries([entry], rag_model=None)

        assert result == [intermediate]

    def test_rag_entry_without_rag_model_and_no_intermediate_results_skipped(self):
        from utils.converters import convert_conversation_entries_to_conversation_entries

        entry = _make_entry(
            status=RetrieveConversationEntryStatuses.COMPLETE,
            action_type=ConversationActionType.RAG,
            intermediate_results=None,
        )

        result = convert_conversation_entries_to_conversation_entries([entry], rag_model=None)

        assert result == []

    def test_rag_entry_with_rag_model_but_no_rag_pipeline_output_skipped(self):
        from utils.converters import convert_conversation_entries_to_conversation_entries

        entry = _make_entry(
            status=RetrieveConversationEntryStatuses.COMPLETE,
            action_type=ConversationActionType.RAG,
            system_output={"other_key": "value"},
        )

        result = convert_conversation_entries_to_conversation_entries([entry], rag_model="RagServiceOutput")

        assert result == []

    def test_intent_entry_with_intent_model_appended(self):
        from utils.converters import convert_conversation_entries_to_conversation_entries

        intent_output = {"intent": "legal"}
        entry = _make_entry(
            status=RetrieveConversationEntryStatuses.COMPLETE,
            action_type=ConversationActionType.INTENT,
            system_output=intent_output,
        )

        result = convert_conversation_entries_to_conversation_entries([entry], intent_model="IntentModel")

        assert len(result) == 1
        assert result[0]["type"] == "IntentModel"
        assert result[0]["data"] == intent_output

    def test_intent_entry_with_intent_model_but_no_system_output_skipped(self):
        from utils.converters import convert_conversation_entries_to_conversation_entries

        entry = _make_entry(
            status=RetrieveConversationEntryStatuses.COMPLETE,
            action_type=ConversationActionType.INTENT,
            system_output=None,
        )

        result = convert_conversation_entries_to_conversation_entries([entry], intent_model="IntentModel")

        assert result == []

    def test_non_complete_entries_are_skipped(self):
        from utils.converters import convert_conversation_entries_to_conversation_entries

        entry = _make_entry(
            status=RetrieveConversationEntryStatuses.FAILED,
            action_type=ConversationActionType.RAG,
            system_output={"rag_pipeline_output": {}},
        )

        result = convert_conversation_entries_to_conversation_entries([entry], rag_model="RagServiceOutput")

        assert result == []

    def test_entries_sorted_by_timestamp(self):
        from utils.converters import convert_conversation_entries_to_conversation_entries

        intermediate_a = {"order": "a"}
        intermediate_b = {"order": "b"}
        entry_later = _make_entry(
            status=RetrieveConversationEntryStatuses.COMPLETE,
            action_type=ConversationActionType.RAG,
            intermediate_results=intermediate_a,
            timestamp=2,
        )
        entry_earlier = _make_entry(
            status=RetrieveConversationEntryStatuses.COMPLETE,
            action_type=ConversationActionType.RAG,
            intermediate_results=intermediate_b,
            timestamp=1,
        )

        result = convert_conversation_entries_to_conversation_entries(
            [entry_later, entry_earlier], rag_model=None
        )

        assert result[0] == intermediate_b
        assert result[1] == intermediate_a
