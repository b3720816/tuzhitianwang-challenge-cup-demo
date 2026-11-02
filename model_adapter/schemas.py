from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


RiskLevel = Literal["low", "medium", "high"]


class GraphNode(BaseModel):
    id: str
    label: str
    risk_level: RiskLevel
    risk_score: float = Field(ge=0.0, le=1.0)
    role: str
    relation: str
    communication_count: int = Field(ge=0)
    is_suspected_group: bool = False


class GraphEdge(BaseModel):
    source: str
    target: str
    weight: float = Field(ge=0)
    relation: str
    time_window: str = ""


class RiskAssessmentResult(BaseModel):
    user_id: str
    display_name: str = ""
    anomaly_score: float = Field(ge=0.0, le=1.0)
    risk_level: RiskLevel
    attribute_curvature: float = Field(ge=0.0, le=1.0)
    neighbor_risk_ratio: float = Field(ge=0.0, le=1.0)
    similarity_gap: float = Field(ge=0.0, le=1.0)
    behavior_deviation: float = Field(ge=0.0, le=1.0)
    high_risk_neighbors: int = Field(ge=0)
    suspected_group_size: int = Field(ge=0)
    related_nodes: list[GraphNode]
    graph_edges: list[GraphEdge]
    abnormal_behaviors: list[str]
    evidence: list[str]
    group_features: dict[str, Any]
    review_suggestion: str
    data_source: str = "prototype_demo"
    is_demo_data: bool = True
