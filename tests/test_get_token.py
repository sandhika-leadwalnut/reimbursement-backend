from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from api.dependencies.auth import get_token

_app = FastAPI()

@_app.get("/_token")
def _echo_token(token: str = Depends(get_token)):
    return {"token": token}

client = TestClient(_app)

def test_cookie_with_csrf_header_is_accepted():
    resp = client.get(
        "/_token",
        cookies={"sb_access_token": "cookie-token"},
        headers={"X-Requested-With": "XMLHttpRequest"},
    )
    assert resp.status_code == 200
    assert resp.json() == {"token": "cookie-token"}

def test_cookie_without_csrf_header_is_rejected():
    resp = client.get("/_token", cookies={"sb_access_token": "cookie-token"})
    assert resp.status_code == 403

def test_no_cookie_is_unauthenticated():
    resp = client.get("/_token")
    assert resp.status_code == 401

def test_bearer_header_alone_no_longer_works():
    resp = client.get("/_token", headers={"Authorization": "Bearer bearer-token"})
    assert resp.status_code == 401
