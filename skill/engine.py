from __future__ import annotations

from typing import Any, Iterable

from model_adapter.schemas import RiskAssessmentResult

from .providers import LLMProvider, LLMProviderError
from .schemas import AssessmentReport, EvidenceCard, EvidenceTraceItem, GroupTrace, NodeRiskAssessment


RISK_LABELS = {"low": "低风险", "medium": "中风险", "high": "高风险"}
LEVEL_CONCLUSIONS = {
    "low": "当前对象风险指标整体处于低位，未发现稳定疑似团伙结构。",
    "medium": "当前对象存在一定异常关系和行为偏离，建议进入普通复核队列。",
    "high": "当前对象风险指标显著偏高，并与多个高风险节点存在密集关联，建议进入重点复核流程。",
}
BOUNDARY_STATEMENT = "本报告由合成样例字段和示意图关系生成，用于竞赛 Demo 展示，不代表真实运营商生产数据、司法认定或昇腾性能结果。"
REPORT_REQUIRED_HEADINGS = ["## 样例事实", "## 系统推断", "## 复核建议", "## 数据与生成边界"]


def _require_result(result: RiskAssessmentResult) -> None:
    if not result.user_id:
        raise ValueError("RiskAssessmentResult.user_id 不能为空")
    if not result.related_nodes:
        raise ValueError(f"{result.user_id} 缺少 related_nodes，无法进行关系研判")


def _join_numbered(items: Iterable[str]) -> str:
    return "\n".join(f"{idx}. {item}" for idx, item in enumerate(items, start=1))


def _join_trace(items: Iterable[EvidenceTraceItem]) -> str:
    lines = []
    for idx, item in enumerate(items, start=1):
        refs = _format_metric_refs(item.metric_refs)
        suffix = f"（字段来源：{','.join(item.source_fields)}；{refs}）" if refs else f"（字段来源：{','.join(item.source_fields)}）"
        lines.append(f"{idx}. {item.text}{suffix}")
    return "\n".join(lines)


def _format_metric_refs(metric_refs: dict[str, Any]) -> str:
    formatted = []
    for key, value in metric_refs.items():
        if isinstance(value, float):
            formatted.append(f"{key}={value:.4f}")
        else:
            formatted.append(f"{key}={value}")
    return "；".join(formatted)


def _evidence_metric_refs(text: str, result: RiskAssessmentResult) -> tuple[list[str], dict[str, float | int | str | bool | None]]:
    source_fields: list[str] = []
    metric_refs: dict[str, float | int | str | bool | None] = {}
    if "异常分数" in text or "置信分数" in text:
        source_fields.extend(["anomaly_score", "risk_level"])
        metric_refs["anomaly_score"] = result.anomaly_score
        metric_refs["risk_level"] = result.risk_level
    if "邻居" in text or "邻居风险" in text:
        source_fields.extend(["neighbor_risk_ratio", "high_risk_neighbors"])
        metric_refs["neighbor_risk_ratio"] = result.neighbor_risk_ratio
        metric_refs["high_risk_neighbors"] = result.high_risk_neighbors
    if "相似度" in text or "风险差" in text:
        source_fields.append("similarity_gap")
        metric_refs["similarity_gap"] = result.similarity_gap
    if "行为" in text or "夜间" in text:
        source_fields.append("behavior_deviation")
        metric_refs["behavior_deviation"] = result.behavior_deviation
    if "属性曲率" in text or "特征" in text:
        source_fields.append("attribute_curvature")
        metric_refs["attribute_curvature"] = result.attribute_curvature
    if "团伙" in text or "图谱" in text or "邻域" in text:
        source_fields.extend(["suspected_group_size", "group_features"])
        metric_refs["suspected_group_size"] = result.suspected_group_size
        metric_refs["group_id"] = result.group_features.get("group_id")
    if not source_fields:
        source_fields = ["evidence", "data_source"]
        metric_refs["data_source"] = result.data_source
    return list(dict.fromkeys(source_fields)), metric_refs


def _build_evidence_trace(result: RiskAssessmentResult, group_trace: GroupTrace) -> list[EvidenceTraceItem]:
    trace: list[EvidenceTraceItem] = []
    for text in result.evidence:
        source_fields, metric_refs = _evidence_metric_refs(text, result)
        trace.append(
            EvidenceTraceItem(
                category="model_fact",
                text=text,
                source_fields=source_fields,
                metric_refs=metric_refs,
                confidence="measured" if "代理" not in text else "derived",
            )
        )
    for text in result.abnormal_behaviors:
        trace.append(
            EvidenceTraceItem(
                category="system_inference",
                text=text,
                source_fields=["abnormal_behaviors", "related_nodes", "group_features"],
                metric_refs={
                    "risk_level": result.risk_level,
                    "high_risk_neighbors": result.high_risk_neighbors,
                    "suspected_group_size": result.suspected_group_size,
                },
                confidence="derived",
            )
        )
    trace.append(
        EvidenceTraceItem(
            category="review_suggestion",
            text=result.review_suggestion,
            source_fields=["review_suggestion", "risk_level", "group_features"],
            metric_refs={
                "risk_level": result.risk_level,
                "group_id": group_trace.group_id,
                "core_node": group_trace.core_node,
            },
            confidence="advisory",
        )
    )
    return trace


def _trace_by_category(items: list[EvidenceTraceItem], category: str) -> list[EvidenceTraceItem]:
    return [item for item in items if item.category == category]


def assess_node_risk(result: RiskAssessmentResult) -> NodeRiskAssessment:
    _require_result(result)
    conclusion = LEVEL_CONCLUSIONS[result.risk_level]
    metric_explanations = [
        f"异常分数为 {result.anomaly_score:.2f}，风险等级为{RISK_LABELS[result.risk_level]}。",
        f"邻居风险比例为 {result.neighbor_risk_ratio:.0%}，高风险邻居数量为 {result.high_risk_neighbors}。",
        f"属性曲率为 {result.attribute_curvature:.2f}，节点-子图相似度差为 {result.similarity_gap:.2f}。",
        f"行为偏离度为 {result.behavior_deviation:.2f}，疑似团伙规模为 {result.suspected_group_size}。",
    ]
    return NodeRiskAssessment(
        user_id=result.user_id,
        risk_level=result.risk_level,
        anomaly_score=result.anomaly_score,
        conclusion=conclusion,
        metric_explanations=metric_explanations,
        abnormal_behaviors=list(result.abnormal_behaviors),
        review_suggestion=result.review_suggestion,
        source_fields=[
            "risk_level",
            "anomaly_score",
            "neighbor_risk_ratio",
            "high_risk_neighbors",
            "attribute_curvature",
            "similarity_gap",
            "behavior_deviation",
            "suspected_group_size",
            "abnormal_behaviors",
            "review_suggestion",
        ],
        data_source=result.data_source,
        is_demo_data=result.is_demo_data,
    )


def trace_fraud_group(result: RiskAssessmentResult) -> GroupTrace:
    _require_result(result)
    group = result.group_features
    related_nodes = list(result.related_nodes)
    edges = list(result.graph_edges)
    group_id = group.get("group_id")
    core_node = group.get("core_node")
    member_count = int(group.get("member_count") or result.suspected_group_size or 0)
    high_risk_member_count = int(group.get("high_risk_member_count") or 0)
    density = float(group.get("density") or 0.0)
    features = list(group.get("features") or ["未发现稳定疑似团伙结构"])
    if group_id:
        summary = (
            f"目标对象关联到疑似团伙 {group_id}，核心节点为 {core_node or '未确定'}，"
            f"成员数量 {member_count}，高风险成员 {high_risk_member_count}，关系密度 {density:.2f}。"
        )
    else:
        summary = "当前对象未归入稳定疑似团伙，关系证据主要来自直接邻居和风险指标。"
    return GroupTrace(
        user_id=result.user_id,
        group_id=group_id,
        core_node=core_node,
        member_count=member_count,
        high_risk_member_count=high_risk_member_count,
        high_risk_neighbors=result.high_risk_neighbors,
        density=density,
        features=features,
        related_nodes=related_nodes,
        edges=edges,
        summary=summary,
        source_fields=[
            "group_features",
            "related_nodes",
            "graph_edges",
            "suspected_group_size",
            "high_risk_neighbors",
        ],
    )


def build_evidence_card(result: RiskAssessmentResult) -> EvidenceCard:
    _require_result(result)
    group_trace = trace_fraud_group(result)
    evidence_trace = _build_evidence_trace(result, group_trace)
    return EvidenceCard(
        user_id=result.user_id,
        risk_level=result.risk_level,
        anomaly_score=result.anomaly_score,
        core_metrics={
            "attribute_curvature": result.attribute_curvature,
            "neighbor_risk_ratio": result.neighbor_risk_ratio,
            "similarity_gap": result.similarity_gap,
            "behavior_deviation": result.behavior_deviation,
            "high_risk_neighbors": result.high_risk_neighbors,
            "suspected_group_size": result.suspected_group_size,
        },
        evidence=list(result.evidence),
        abnormal_behaviors=list(result.abnormal_behaviors),
        evidence_trace=evidence_trace,
        group_trace=group_trace,
        review_suggestion=result.review_suggestion,
        data_source=result.data_source,
        is_demo_data=result.is_demo_data,
        source_fields=[
            "anomaly_score",
            "risk_level",
            "attribute_curvature",
            "neighbor_risk_ratio",
            "similarity_gap",
            "behavior_deviation",
            "high_risk_neighbors",
            "suspected_group_size",
            "evidence",
            "abnormal_behaviors",
            "group_features",
            "review_suggestion",
            "data_source",
            "is_demo_data",
        ],
    )


class RuleBasedLLMProvider:
    """Deterministic provider used before a real model is connected."""

    provider_name = "evidence_constrained_rule_template_v2"

    def generate_report(self, prompt: str, *, evidence_text: str) -> str:
        return prompt


def _report_prompt(result: RiskAssessmentResult, assessment: NodeRiskAssessment, evidence_card: EvidenceCard, group_trace: GroupTrace) -> str:
    group_id = group_trace.group_id or "未发现稳定疑似团伙"
    group_features = "；".join(group_trace.features)
    model_facts = _join_trace(_trace_by_category(evidence_card.evidence_trace, "model_fact"))
    inferences = _join_trace(_trace_by_category(evidence_card.evidence_trace, "system_inference"))
    review_items = _join_trace(_trace_by_category(evidence_card.evidence_trace, "review_suggestion"))
    metric_lines = _join_numbered(assessment.metric_explanations)
    return f"""# 图织天网智能研判报告

## 研判对象

- 用户编号：{result.user_id}
- 样例名称：{result.display_name}
- 数据来源：{result.data_source}
- 原型演示数据：{"是" if result.is_demo_data else "否"}

## 风险结论

{assessment.conclusion}

{metric_lines}

## 样例事实

{model_facts}

## 系统推断

{inferences}

## 疑似团伙关系

- 团伙标识：{group_id}
- 疑似团伙规模：{result.suspected_group_size}
- 团伙核心节点：{group_trace.core_node or "无"}
- 高风险成员数：{group_trace.high_risk_member_count}
- 关系密度：{group_trace.density:.2f}
- 团伙特征：{group_features}

## 复核建议

{review_items}

## 数据与生成边界

{BOUNDARY_STATEMENT}
"""


def _guard_report_text(report: str, *, fallback_prompt: str) -> tuple[str, list[str]]:
    warnings: list[str] = []
    guarded = (report or "").strip()
    if not guarded:
        guarded = fallback_prompt
        warnings.append("provider 返回空内容，已回退到规则模板。")
    for heading in REPORT_REQUIRED_HEADINGS:
        if heading not in guarded:
            warnings.append(f"provider 输出缺少必要章节 {heading}，已保留安全提示。")
            break
    if BOUNDARY_STATEMENT not in guarded:
        guarded = f"{guarded.rstrip()}\n\n## 数据与生成边界\n\n{BOUNDARY_STATEMENT}\n"
        warnings.append("provider 输出缺少真实性边界声明，已自动补充。")
    return guarded, warnings


def generate_assessment_report(result: RiskAssessmentResult, provider: LLMProvider | None = None) -> AssessmentReport:
    _require_result(result)
    assessment = assess_node_risk(result)
    group_trace = trace_fraud_group(result)
    evidence_card = build_evidence_card(result)
    provider = provider or RuleBasedLLMProvider()
    prompt = _report_prompt(result, assessment, evidence_card, group_trace)
    evidence_text = "\n".join(
        [
            *[item.text for item in _trace_by_category(evidence_card.evidence_trace, "model_fact")],
            *[item.text for item in _trace_by_category(evidence_card.evidence_trace, "system_inference")],
            *[item.text for item in _trace_by_category(evidence_card.evidence_trace, "review_suggestion")],
            group_trace.summary,
        ]
    )
    provider_name = getattr(provider, "provider_name", provider.__class__.__name__)
    provider_warnings: list[str] = []
    try:
        raw_report = provider.generate_report(prompt, evidence_text=evidence_text)
    except LLMProviderError as exc:
        raw_report = prompt
        provider_name = f"evidence_constrained_rule_template_v2:fallback_from:{provider_name}"
        provider_warnings.append(f"千问 Provider 调用失败或输出越界：{exc}；已回退到证据约束规则模板。")
    except (TimeoutError, OSError, ValueError):
        raw_report = prompt
        provider_name = f"evidence_constrained_rule_template_v2:fallback_from:{provider_name}"
        provider_warnings.append("千问 Provider 发生非预期运行错误，已回退到证据约束规则模板。")
    report, safety_warnings = _guard_report_text(raw_report, fallback_prompt=prompt)
    return AssessmentReport(
        user_id=result.user_id,
        report=report,
        evidence_card=evidence_card,
        node_assessment=assessment,
        group_trace=group_trace,
        generated_by=provider_name,
        data_source=result.data_source,
        is_demo_data=result.is_demo_data,
        source_fields=[
            "RiskAssessmentResult",
            "NodeRiskAssessment",
            "GroupTrace",
            "EvidenceCard",
            "EvidenceTraceItem",
        ],
        safety_warnings=[*provider_warnings, *safety_warnings],
    )
