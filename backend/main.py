from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from model_adapter.demo_adapter import list_demo_users, assess_user_risk, get_user_graph, DemoUserNotFound
from skill import assess_node_risk, trace_fraud_group, build_evidence_card, generate_assessment_report, RuleBasedLLMProvider
ROOT=Path(__file__).resolve().parents[1]
app=FastAPI(title='图织天网 · 合成样例演示')
@app.get('/api/health')
def health(): return {'service':'ok','mode':'synthetic_demo','runtime_model_inference':False}
@app.get('/api/llm/status')
def llm_status(): return {'mode':'rule_template','configured':True,'external_requests':False}
@app.get('/api/users')
def users(): return list_demo_users()
def resolve(user_id):
    try: return assess_user_risk(user_id)
    except DemoUserNotFound: raise HTTPException(404,'未知合成样例编号')
@app.get('/api/users/{user_id}/risk')
def risk(user_id:str):
    r=resolve(user_id);return {**r.model_dump(),'node_assessment':assess_node_risk(r).model_dump(),'group_trace':trace_fraud_group(r).model_dump(),'evidence_card':build_evidence_card(r).model_dump()}
@app.get('/api/users/{user_id}/graph')
def graph(user_id:str):
    resolve(user_id);return get_user_graph(user_id)
@app.get('/api/users/{user_id}/evidence-card')
def evidence(user_id:str): return build_evidence_card(resolve(user_id)).model_dump()
@app.post('/api/users/{user_id}/report')
def report(user_id:str): return generate_assessment_report(resolve(user_id),provider=RuleBasedLLMProvider()).model_dump()
if (ROOT/'frontend/dist').exists(): app.mount('/',StaticFiles(directory=ROOT/'frontend/dist',html=True),name='frontend')
