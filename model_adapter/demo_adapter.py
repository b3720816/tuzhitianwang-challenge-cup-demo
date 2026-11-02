from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from skill import build_evidence_card as skill_build_evidence_card
from skill import generate_assessment_report

from .schemas import RiskAssessmentResult


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "demo"
CASE_FILES = {
    "U1001": DATA_DIR / "low_risk.json",
    "U1002": DATA_DIR / "medium_risk.json",
    "U1003": DATA_DIR / "high_risk.json",
}


class DemoUserNotFound(KeyError):
    pass


@lru_cache(maxsize=1)
def _load_cases() -> dict[str, RiskAssessmentResult]:
    cases: dict[str, RiskAssessmentResult] = {}
    for path in CASE_FILES.values():
        payload = json.loads(path.read_text(encoding="utf-8"))
        result = RiskAssessmentResult.model_validate(payload)
        cases[result.user_id] = result
    return cases


def _case(user_id: str) -> RiskAssessmentResult:
    item = _load_cases().get(user_id)
    if item is None:
        raise DemoUserNotFound(user_id)
    return item


def list_demo_users() -> list[dict[str, Any]]:
    order = {"low": 0, "medium": 1, "high": 2}
    return [
        {
            "user_id": item.user_id,
            "display_name": item.display_name,
            "risk_level": item.risk_level,
            "anomaly_score": item.anomaly_score,
            "summary": item.evidence[0] if item.evidence else "",
            "data_source": item.data_source,
            "is_demo_data": item.is_demo_data,
        }
        for item in sorted(_load_cases().values(), key=lambda case: order[case.risk_level])
    ]


def assess_user_risk(user_id: str) -> RiskAssessmentResult:
    return _case(user_id)


def get_user_graph(user_id: str) -> dict[str, Any]:
    result = _case(user_id)
    return {
        "user_id": result.user_id,
        "nodes": [node.model_dump() for node in result.related_nodes],
        "edges": [edge.model_dump() for edge in result.graph_edges],
        "is_demo_data": result.is_demo_data,
        "data_source": result.data_source,
    }


def build_evidence_card(result: RiskAssessmentResult) -> dict[str, Any]:
    return skill_build_evidence_card(result).model_dump()


def generate_user_report(user_id: str) -> dict[str, Any]:
    result = _case(user_id)
    return generate_assessment_report(result).model_dump()
