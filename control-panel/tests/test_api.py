"""Tests for the API endpoints — scan creation, scope validation, cancellation, finding status."""
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.database import init_db


@pytest.fixture
def client():
    from app.main import app
    init_db()
    with TestClient(app) as c:
        yield c


class TestScopeValidation:
    def test_valid_scope_accepted(self, client):
        resp = client.post("/api/scans/validate-scope", json={
            "scope": "10.10.20.0/24",
            "profile": "safe",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is True
        assert "10.10.20.0/24" in data["cidrs"]
        assert data["address_count"] == 256
        assert data["scope_id"] is not None

    def test_invalid_scope_rejected(self, client):
        resp = client.post("/api/scans/validate-scope", json={
            "scope": "not-an-ip",
            "profile": "safe",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is False
        assert "error" in data

    def test_loopback_rejected(self, client):
        resp = client.post("/api/scans/validate-scope", json={
            "scope": "127.0.0.0/8",
            "profile": "safe",
        })
        data = resp.json()
        assert data["valid"] is False

    def test_too_broad_rejected(self, client):
        resp = client.post("/api/scans/validate-scope", json={
            "scope": "10.0.0.0/8",
            "profile": "safe",
        })
        data = resp.json()
        assert data["valid"] is False

    def test_invalid_profile_rejected(self, client):
        resp = client.post("/api/scans/validate-scope", json={
            "scope": "10.10.20.0/24",
            "profile": "nonexistent",
        })
        assert resp.status_code == 422


class TestScanCreation:
    def test_create_scan_requires_valid_scope_id(self, client):
        resp = client.post("/api/scans", json={
            "scope_id": "nonexistent",
            "profile": "safe",
        })
        assert resp.status_code == 404

    def test_create_scan_after_validation(self, client):
        resp = client.post("/api/scans/validate-scope", json={
            "scope": "10.10.20.0/24",
            "profile": "safe",
        })
        scope_id = resp.json()["scope_id"]

        with patch("app.api.scans.enqueue_scan"):
            resp = client.post("/api/scans", json={
                "scope_id": scope_id,
                "profile": "safe",
            })
        assert resp.status_code == 201
        data = resp.json()
        assert data["id"].startswith("scan-")
        assert data["status"] == "PENDING"
        assert data["profile"] == "safe"

    def test_list_scans(self, client):
        with patch("app.api.scans.enqueue_scan"):
            resp = client.post("/api/scans/validate-scope", json={"scope": "10.10.20.0/24", "profile": "safe"})
            scope_id = resp.json()["scope_id"]
            client.post("/api/scans", json={"scope_id": scope_id, "profile": "safe"})

        resp = client.get("/api/scans")
        assert resp.status_code == 200
        scans = resp.json()
        assert len(scans) >= 1

    def test_get_scan_detail(self, client):
        with patch("app.api.scans.enqueue_scan"):
            resp = client.post("/api/scans/validate-scope", json={"scope": "10.10.20.0/24", "profile": "safe"})
            scope_id = resp.json()["scope_id"]
            create_resp = client.post("/api/scans", json={"scope_id": scope_id, "profile": "safe"})
            scan_id = create_resp.json()["id"]

        resp = client.get(f"/api/scans/{scan_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == scan_id
        assert "stages" in data
        assert "logs" in data

    def test_get_nonexistent_scan(self, client):
        resp = client.get("/api/scans/scan-9999-999999")
        assert resp.status_code == 404


class TestScanCancellation:
    def test_cancel_pending_scan(self, client):
        with patch("app.api.scans.enqueue_scan"), patch("app.api.scans.set_cancelled"):
            resp = client.post("/api/scans/validate-scope", json={"scope": "10.10.20.0/24", "profile": "safe"})
            scope_id = resp.json()["scope_id"]
            create_resp = client.post("/api/scans", json={"scope_id": scope_id, "profile": "safe"})
            scan_id = create_resp.json()["id"]

        with patch("app.api.scans.set_cancelled"):
            resp = client.post(f"/api/scans/{scan_id}/cancel")
        assert resp.status_code == 200
        assert resp.json()["status"] == "CANCELLED"

    def test_cancel_nonexistent_scan(self, client):
        resp = client.post("/api/scans/scan-9999-999999/cancel")
        assert resp.status_code == 404


class TestFindingStatus:
    def test_update_finding_status(self, client):
        from app.database import get_session
        from app.models import Finding, FindingStatus

        with get_session() as session:
            f = Finding(
                dedup_key="test-key",
                title="Test finding",
                severity="HIGH",
                confidence="HIGH",
                source="nuclei",
                status=FindingStatus.OPEN.value,
            )
            session.add(f)
            session.flush()
            finding_id = f.id

        resp = client.post(f"/api/findings/{finding_id}/status", json={
            "status": "CONFIRMED",
            "reason": "Verified manually",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "CONFIRMED"
        assert data["old_status"] == "OPEN"

    def test_invalid_finding_status(self, client):
        from app.database import get_session
        from app.models import Finding

        with get_session() as session:
            f = Finding(
                dedup_key="test-key-2",
                title="Test",
                severity="LOW",
                confidence="HIGH",
                source="nuclei",
            )
            session.add(f)
            session.flush()
            finding_id = f.id

        resp = client.post(f"/api/findings/{finding_id}/status", json={"status": "INVALID"})
        assert resp.status_code == 400

    def test_add_finding_note(self, client):
        from app.database import get_session
        from app.models import Finding

        with get_session() as session:
            f = Finding(
                dedup_key="test-key-3",
                title="Test",
                severity="LOW",
                confidence="HIGH",
                source="nuclei",
            )
            session.add(f)
            session.flush()
            finding_id = f.id

        resp = client.post(f"/api/findings/{finding_id}/notes", json={
            "note": "This looks like a false positive",
            "author": "analyst",
        })
        assert resp.status_code == 200
        assert resp.json()["note"] == "This looks like a false positive"


class TestSecurityBoundaries:
    """Test that the system cannot start out-of-scope scans or bypass scope validation."""

    def test_out_of_scope_scan_rejected_at_api(self, client):
        resp = client.post("/api/scans/validate-scope", json={
            "scope": "127.0.0.0/8",
            "profile": "safe",
        })
        assert resp.json()["valid"] is False

    def test_scope_validation_required_before_scan(self, client):
        resp = client.post("/api/scans", json={
            "scope_id": "fake-id",
            "profile": "safe",
        })
        assert resp.status_code == 404

    def test_worker_scope_enforcement(self):
        """Workers must check every target against the scope."""
        from app.scope import ScopeManager
        sm = ScopeManager()
        scope = sm.parse("10.10.20.0/24")
        with pytest.raises(Exception, match="outside the authorised scope"):
            sm.assert_in_scope(scope, "192.168.99.1")
