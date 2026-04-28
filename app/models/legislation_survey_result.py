from typing import List, Optional
from pydantic import Field, BaseModel


class Xpath(BaseModel):
    index: Optional[int] = None
    isHeader: Optional[bool] = False
    isFooter: Optional[bool] = False
    xpath: str


class LegislationSurveyUserInput(BaseModel):
    question: str
    fermi_jurisdictions: Optional[List[str]] = ["ALL_CASES"]


class LegislationSurveyCite(BaseModel):
    start_offset: int
    end_offset: int
    doc_guid: str


class LegislationSurveySummary(BaseModel):
    summary_text: str
    cites: List[LegislationSurveyCite] = Field(default_factory=list)


class LegislationSurveySearchInfo(BaseModel):
    index: str
    query: str
    search_type: str
    rank: int
    score: float


class LegislationSurveyScoredPassage(BaseModel):
    passage_id: str
    passage_text: str
    indexed_xpath: Optional[str] = None
    search_info: List[LegislationSurveySearchInfo]
    in_input: bool = False


class LegislationSurveySource(BaseModel):
    doc_guid: str
    content_type: Optional[str] = None
    fermi_jurisdictions: List[str]
    doc_serial_number: Optional[str] = None
    collection_name: Optional[str] = None
    title: str
    passages: List[LegislationSurveyScoredPassage] = Field(default_factory=list)


class LegislationSurveyAnswer(BaseModel):
    content_type: Optional[str] = None
    jurisdiction: str
    answer_text: str
    sources: List[LegislationSurveySource] = Field(default_factory=list)
    cites: List[LegislationSurveyCite] = Field(default_factory=list)


class LegislationSurveyResult(BaseModel):
    """Definition for legislation survey request output. """
    user_input: LegislationSurveyUserInput = Field(default=None)
    summary: LegislationSurveySummary = Field(default=None)
    answers: List[LegislationSurveyAnswer] = Field(default_factory=list)
