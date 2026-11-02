"""Prepare a browser-only build from the public synthetic demo fixtures.

Run in an isolated checkout before Vite. The Python API remains the default
for normal local development; only VITE_STATIC_DEMO=true uses these snapshots.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from model_adapter.demo_adapter import assess_user_risk, get_user_graph, list_demo_users
from skill import assess_node_risk, build_evidence_card, generate_assessment_report, trace_fraud_group


def main():
    users = list_demo_users()
    assert {user["user_id"] for user in users} == {"U1001", "U1002", "U1003"}
    assert all(user["is_demo_data"] for user in users)
    snapshots = {
        "/api/health": {"service": "ok", "mode": "static_synthetic_demo", "runtime_model_inference": False},
        "/api/llm/status": {"mode": "rule_template_snapshot", "configured": True, "external_requests": False},
        "/api/users": users,
    }
    for user in users:
        uid = user["user_id"]
        result = assess_user_risk(uid)
        prefix = f"/api/users/{uid}"
        snapshots[prefix + "/risk"] = {
            **result.model_dump(),
            "node_assessment": assess_node_risk(result).model_dump(),
            "group_trace": trace_fraud_group(result).model_dump(),
            "evidence_card": build_evidence_card(result).model_dump(),
        }
        snapshots[prefix + "/graph"] = get_user_graph(uid)
        snapshots[prefix + "/evidence-card"] = build_evidence_card(result).model_dump()
        snapshots[prefix + "/report"] = generate_assessment_report(result).model_dump()

    target = ROOT / "frontend/public/demo/api.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(snapshots, ensure_ascii=False), encoding="utf-8")

    client = ROOT / "frontend/src/api/client.ts"
    source = client.read_text(encoding="utf-8")
    marker = "export async function api(path: string, options: ApiOptions = {}) {"
    assert source.count(marker) == 1
    static_client = '''
  // Public browser demo: precomputed synthetic fixtures, never live inference.
  if (import.meta.env.VITE_STATIC_DEMO === 'true') {
    if (!staticSnapshots) {
      staticSnapshots = fetch(import.meta.env.BASE_URL + 'demo/api.json')
        .then(async response => {
          if (!response.ok) throw new Error('合成样例加载失败，请刷新重试')
          return await response.json()
        }).catch(error => { staticSnapshots = null; throw error })
    }
    const snapshots = await staticSnapshots
    const method = (options.method || 'GET').toUpperCase()
    if ((method !== 'GET' && !(method === 'POST' && path.endsWith('/report')))
        || !Object.prototype.hasOwnProperty.call(snapshots, path)) {
      throw new Error('未知合成样例编号，请选择 U1001、U1002 或 U1003')
    }
    return structuredClone(snapshots[path])
  }
'''
    if "let staticSnapshots:" not in source:
        source = "let staticSnapshots: Promise<Record<string, any>> | null = null" + chr(10) + source
        source = source.replace(marker, marker + static_client)
        client.write_text(source, encoding="utf-8")

    view = ROOT / "frontend/src/views/DemoWorkbench.vue"
    text = view.read_text(encoding="utf-8")
    replacements = {
        "本机功能演示链路": "网页功能演示链路",
        "本机接口耗时：": "页面处理耗时：",
        "本地规则模板": "规则模板预生成结果",
        "value:'本地服务',detail:'无需云端接口或 API Key'": "value:'浏览器演示',detail:'无需安装；读取合成样例与预生成报告'",
        "模板整理固定字段，未调用大语言模型": "展示固定字段与预生成报告，未调用大语言模型",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    view.write_text(text, encoding="utf-8")
    print(f"Prepared {len(users)} synthetic cases and {len(snapshots)} demo routes.")


if __name__ == "__main__":
    main()
