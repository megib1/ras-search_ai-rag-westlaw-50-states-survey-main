from legislation_survey.dataclasses import LegislationSurveyServiceOutput
from conversation_core.shared.enums import RetrieveConversationEntryStatuses, ConversationActionType
from conversation_core.shared.enums import IntentClassification

from models.legislation_survey_result import (
    LegislationSurveyResult, LegislationSurveyUserInput, LegislationSurveySummary, LegislationSurveyAnswer,
    LegislationSurveyCite, LegislationSurveySource
)



def convert_ls_labs_output_to_ls_survey_result(labs_output: LegislationSurveyServiceOutput) -> LegislationSurveyResult:

    user_input = LegislationSurveyUserInput(**labs_output.user_input.model_dump(exclude_none=True, exclude_unset=True))

    summary_cites = []
    for cite in labs_output.summary.cites:
        summary_cites.append(LegislationSurveyCite(**cite.model_dump(exclude_none=True, exclude_unset=True)))
    summary = LegislationSurveySummary(summary_text=labs_output.summary.summary_text,
                                       cites=summary_cites)

    answers = []
    for ans in labs_output.answers:
        sources = [LegislationSurveySource(**source.model_dump(exclude_none=True, exclude_unset=True)) for source in ans.sources]
        cites = [LegislationSurveyCite(**cite.model_dump(exclude_none=True, exclude_unset=True)) for cite in ans.cites]
        answers.append(LegislationSurveyAnswer(content_type=ans.content_type,
                                               jurisdiction=ans.jurisdiction,
                                               answer_text=ans.answer_text,
                                               sources=sources,
                                               cites=cites))

    return LegislationSurveyResult(user_input=user_input,
                                   summary=summary,
                                   answers=answers)


def convert_conversation_entries_to_conversation_entries(conversation_history,
                                                         intent_model: str = None,
                                                         rag_model: str = None):
    ret_conversation_history = []
    conversation_history.sort(key=lambda entry: entry.timestamp)
    for conversation_entry in conversation_history:
        if (conversation_entry.status == RetrieveConversationEntryStatuses.COMPLETE
                and conversation_entry.result is not None):
            if conversation_entry.result.conversation_action_type == ConversationActionType.RAG:
                if rag_model is None:
                    if conversation_entry.result.intermediate_results is not None:
                        ret_conversation_history.append(conversation_entry.result.intermediate_results)
                else:
                    if conversation_entry.result.system_output is not None and "rag_pipeline_output" in conversation_entry.result.system_output:
                        history_entry: dict = {"type": rag_model,
                                               "data": conversation_entry.result.system_output["rag_pipeline_output"]}
                        history_entry["data"]["user_input"]["content_types"] = \
                            conversation_entry.result.system_output["rag_pipeline_output"]["intent"]["user_input"][
                                "content_types"]  # Labs input has strict user input requirements
                        ret_conversation_history.append(history_entry)
            if (intent_model is not None
                    and conversation_entry.result.conversation_action_type == ConversationActionType.INTENT):
                if conversation_entry.result.system_output is not None:
                    history_entry: dict = {"type": intent_model, "data": conversation_entry.result.system_output}
                    ret_conversation_history.append(history_entry)
    return ret_conversation_history


def convert_conv_entries_to_aalp_conv_history(conversation_entries,
                                              intent_model: str = None,
                                              rag_model: str = None):
    ret_conversation_history: list[dict] = []
    conversation_entries.sort(key=lambda entry: entry.timestamp)
    for conversation_entry in conversation_entries:
        if (conversation_entry.status == RetrieveConversationEntryStatuses.COMPLETE
                and conversation_entry.result is not None):
            if conversation_entry.result.conversation_action_type == ConversationActionType.RAG:
                if rag_model is None:
                    if conversation_entry.result.intermediate_results is not None:
                        ret_conversation_history.append(conversation_entry.result.intermediate_results)
                else:
                    if (conversation_entry.result.system_output is not None
                            and "rag_pipeline_output" in conversation_entry.result.system_output):
                        history_entry: dict = {"type": rag_model,
                                               "data": conversation_entry.result.system_output["rag_pipeline_output"]
                                               }
                        # Labs input has strict user input requirements
                        history_entry["data"]["user_input"]["content_types"] = (
                            conversation_entry.result.system_output["rag_pipeline_output"]["intent"]["user_input"]["content_types"]
                        )
                        ret_conversation_history.append(history_entry)
            if (intent_model is not None
                    and conversation_entry.result.conversation_action_type == ConversationActionType.INTENT):
                if conversation_entry.result.system_output is not None:
                    history_entry: dict = {"type": intent_model, "data": conversation_entry.result.system_output}
                    ret_conversation_history.append(history_entry)
    return ret_conversation_history