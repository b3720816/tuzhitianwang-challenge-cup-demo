from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from model_adapter.schemas import GraphEdge, GraphNode, RiskAssessmentResult, RiskLevel


SkillName = Literal[
    "assess_node_risk",
    "trace_fraud_group",
    "build_evidence_card",
    "generate_assessment_report",
]
EvidenceCategory = Literal["model_fact", "system_inference", "review_suggestion"]
EvidenceConfidence = Literal["measured", "derived", "advisory"]


class SkillError(BaseModel):
    skill: SkillName
    user_id: str | None = None
    message: str
    detail: dict[str, Any] = Field(default_factory=dict)


class NodeRiskAssessment(BaseModel):
    skill: Literal["assess_node_risk"] = "assess_node_risk"
    user_id: str
    risk_level: RiskLevel
    anomaly_score: float
    conclusion: str
    metric_explanations: list[str]
    abnormal_behaviors: list[str]
    review_suggestion: str
    source_fields: list[str]
    data_source: str
    is_demo_data: bool


class GroupTrace(BaseModel):
    skill: Literal["trace_fraud_group"] = "trace_fraud_group"
    user_id: str
    group_id: str | None = None
    core_node: str | None = None
    member_count: int = 0
    high_risk_member_count: int = 0
    high_risk_neighbors: int = 0
    density: float = 0.0
    features: list[str]
    related_nodes: list[GraphNode]
    edges: list[GraphEdge]
    summary: str
    source_fields: list[str]


class EvidenceTraceItem(BaseModel):
    category: EvidenceCategory
    text: str
    source_fields: list[str]
    metric_refs: dict[str, float | int | str | bool | None] = Field(default_factory=dict)
    confidence: EvidenceConfidence


class EvidenceCard(BaseModel):
    skill: Literal["build_evidence_card"] = "build_evidence_card"
    user_id: str
    risk_level: RiskLevel
    anomaly_score: float
    core_metrics: dict[str, float | int]
    evidence: list[str]
    abnormal_behaviors: list[str]
    evidence_trace: list[EvidenceTraceItem]
    group_trace: GroupTrace
    review_suggestion: str
    data_source: str
    is_demo_data: bool
    source_fields: list[str]


class AssessmentReport(BaseModel):
    skill: Literal["generate_assessment_report"] = "generate_assessment_report"
    user_id: str
    report: str
    evidence_card: EvidenceCard
    node_assessment: NodeRiskAssessment
    group_trace: GroupTrace
    generated_by: str
    data_source: str
    is_demo_data: bool
    source_fields: list[str]
    safety_warnings: list[str] = Field(default_factory=list)


class SkillInputExample(BaseModel):
    user_id: str
    input_schema: str = "RiskAssessmentResult"
    sample: RiskAssessmentResult
