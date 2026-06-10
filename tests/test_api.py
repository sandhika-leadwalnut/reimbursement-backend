def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_unauthorized_access(client):
    response = client.get("/me")
    assert response.status_code in (401, 403)

def test_admin_dashboard_unauthorized(client):
    response = client.get("/admin/dashboard")
    assert response.status_code in (401, 403)
