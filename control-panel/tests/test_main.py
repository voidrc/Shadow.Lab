from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from app.main import app, check_tailscale, serialize_container


def test_check_tailscale_requires_running_and_ip():
    result = Mock(returncode=0, stdout='{"BackendState":"Running","Self":{"TailscaleIPs":["100.64.0.1"]}}', stderr="")
    with patch("app.main.subprocess.run", return_value=result):
        status = check_tailscale()
    assert status["healthy"] is True
    assert "100.64.0.1" in status["message"]


def test_check_tailscale_rejects_unauthenticated_node():
    result = Mock(returncode=0, stdout='{"BackendState":"NeedsLogin","Self":{"TailscaleIPs":null}}', stderr="")
    with patch("app.main.subprocess.run", return_value=result):
        status = check_tailscale()
    assert status["healthy"] is False
    assert "no tailnet IP" in status["message"]


def test_serialize_container_includes_health_and_labels():
    container = Mock()
    container.short_id = "abc123"
    container.name = "demo"
    container.status = "running"
    container.labels = {"shadow.lab.name": "Demo", "shadow.lab.description": "Example"}
    container.attrs = {"State": {"Health": {"Status": "healthy"}}}
    result = serialize_container(container)
    assert result["display_name"] == "Demo"
    assert result["health"] == "healthy"


def test_action_rejects_unknown_action():
    status = {"healthy": True, "message": "ok", "checked_at": "now"}
    with patch("app.main.check_tailscale", return_value=status):
        with TestClient(app) as client:
            response = client.post("/api/services/abc/pause")
    assert response.status_code == 400
