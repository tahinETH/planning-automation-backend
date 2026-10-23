"""Keep JSON transfer small without changing authenticated data or Ravi SSE."""
import pytest
from fastapi.testclient import TestClient
from app import main
from app.auth import CurrentUser, current_user

@pytest.fixture
def client(monkeypatch):
    state={'seed': {'orders': [], 'productionHistory': [
        {'id': f'history-{i}', 'product': 'SYNTHETIC', 'quantity': 100, 'status': 'delivered'} for i in range(300)
    ]}, 'updatedAt': 'synthetic-revision'}
    monkeypatch.setattr(main, 'planning_state', lambda: state)
    main.app.dependency_overrides[current_user]=lambda: CurrentUser('synthetic-user','Test','','user')
    try: yield TestClient(main.app),state
    finally: main.app.dependency_overrides.pop(current_user,None)

def test_perf_json_compression_preserves_the_entire_snapshot_and_revision(client):
    http,state=client
    plain=http.get('/api/planning-state',headers={'Accept-Encoding':'identity'})
    compressed=http.get('/api/planning-state',headers={'Accept-Encoding':'gzip'})
    assert plain.status_code==compressed.status_code==200
    assert plain.json()==compressed.json()==state
    assert compressed.headers.get('content-encoding')=='gzip'
    assert int(compressed.headers['content-length']) < len(plain.content)//4
    assert 'accept-encoding' in compressed.headers.get('vary','').lower()

def test_perf_small_health_response_does_not_need_compression(client):
    http,_=client
    response=http.get('/health',headers={'Accept-Encoding':'gzip'})
    assert response.status_code==200
    assert response.json()=={'status':'ok'}
    assert 'content-encoding' not in response.headers
