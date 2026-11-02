import pytest
from fastapi.testclient import TestClient
from backend.main import app
client=TestClient(app)
@pytest.mark.parametrize('user',['U1001','U1002','U1003'])
def test_complete_synthetic_flow(user):
    for name in ['risk','graph','evidence-card']:
        r=client.get(f'/api/users/{user}/{name}');assert r.status_code==200
    result=client.get(f'/api/users/{user}/risk').json();assert result['is_demo_data'] and result['data_source']=='prototype_demo'
    r=client.post(f'/api/users/{user}/report');assert r.status_code==200 and user in r.json()['report']
def test_no_real_data_endpoints():
    assert client.get('/api/real-users').status_code!=200
    assert client.get('/api/users/REAL_HIGH/risk').status_code==404
    assert client.get('/api/health').json()['runtime_model_inference'] is False
