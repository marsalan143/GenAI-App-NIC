"""Small, explicit contracts for data received from Groq."""
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
Items = Annotated[list[Text], Field(min_length=1)]

class Schema(BaseModel):
    model_config = ConfigDict(extra='forbid')

class StartupInput(Schema):
    problem: Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=6000)]
    themes: list[str] = []
    audience: str = ''
    market: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=120)] = 'Pakistan'
    budget: Annotated[str, StringConstraints(max_length=200)] = ''

class Concept(Schema):
    approach: Literal['Budget-Friendly', 'Technology-Driven', 'High-Growth']
    name: Text
    tagline: Text
    problem: Text
    solution: Text
    customers: Text
    usp: Text
    revenue_model: Text
    budget: Text
    risks: Items

class Concepts(Schema):
    concepts: list[Concept] = Field(min_length=3, max_length=3)

    @model_validator(mode='after')
    def distinct(self):
        if {c.approach for c in self.concepts} != {'Budget-Friendly', 'Technology-Driven', 'High-Growth'}:
            raise ValueError('Return one concept for each approach.')
        if len({c.name.casefold() for c in self.concepts}) != 3 or len({c.solution.casefold() for c in self.concepts}) != 3:
            raise ValueError('Concepts must be distinct.')
        return self

class Rating(Schema):
    score: float = Field(ge=0, le=100, allow_inf_nan=False)
    reasoning: Text

class Feasibility(Schema):
    market_demand: Rating
    competition: Rating
    investment: Rating
    technical_feasibility: Rating
    scalability: Rating
    summary: Text
    strengths: Items
    weaknesses: Items
    risks: Items
    recommendations: Items
    assumptions_to_validate: Items

class Question(Schema):
    category: Literal['Market demand', 'Revenue and profitability', 'Competition', 'Customer acquisition', 'Scalability and execution']
    question: Text

class Questions(Schema):
    questions: list[Question] = Field(min_length=5, max_length=5)

    @model_validator(mode='after')
    def coverage(self):
        if len({q.category for q in self.questions}) != 5 or len({q.question.casefold() for q in self.questions}) != 5:
            raise ValueError('Five different questions covering all categories are required.')
        return self

class Evaluation(Schema):
    score: float = Field(ge=0, le=10, allow_inf_nan=False)
    answered_well: Items
    weaknesses: Items
    missing_evidence: Items
    suggestions: Items

class ImprovedPlan(Schema):
    markdown: Text
    changes: Items

class Pitch(Schema):
    startup_name: Text
    problem: Text
    solution: Text
    target_market: Text
    business_model: Text
    competitive_advantage: Text
    revenue_strategy: Text
    mvp: Text
    estimated_budget: Text
    funding_requirements: Text
    roadmap_90_days: Text

class Canvas(Schema):
    customer_segments: Items
    value_propositions: Items
    channels: Items
    customer_relationships: Items
    revenue_streams: Items
    key_resources: Items
    key_activities: Items
    key_partnerships: Items
    cost_structure: Items
