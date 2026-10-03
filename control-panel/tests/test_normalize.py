"""Tests for finding normalization and deduplication."""
import json

from app.models import Confidence, Finding, Severity
from app.normalize import (
    deduplicate_findings,
    make_dedup_key,
    map_confidence,
    map_severity,
    normalize_exposure,
    normalize_nuclei,
)


class TestSeverityMapping:
    def test_known_severities(self):
        assert map_severity("critical") == Severity.CRITICAL
        assert map_severity("HIGH") == Severity.HIGH
        assert map_severity("medium") == Severity.MEDIUM
        assert map_severity("low") == Severity.LOW
        assert map_severity("info") == Severity.INFO
        assert map_severity("informational") == Severity.INFO

    def test_unknown_severity_defaults_to_info(self):
        assert map_severity("unknown") == Severity.INFO
        assert map_severity(None) == Severity.INFO
        assert map_severity("nonsense") == Severity.INFO


class TestConfidenceMapping:
    def test_known_confidences(self):
        assert map_confidence("high") == Confidence.HIGH
        assert map_confidence("medium") == Confidence.MEDIUM
        assert map_confidence("low") == Confidence.LOW

    def test_unknown_confidence(self):
        assert map_confidence(None) == Confidence.UNKNOWN
        assert map_confidence("nonsense") == Confidence.UNKNOWN


class TestNucleiNormalization:
    def test_valid_nuclei_finding(self):
        nf = {
            "template_id": "CVE-2021-1234",
            "template_name": "Test Vulnerability",
            "severity": "HIGH",
            "confidence": "high",
            "host": "10.10.20.15",
            "url": "https://10.10.20.15/",
            "matched_at": "https://10.10.20.15/",
            "description": "A test vulnerability",
            "reference": ["https://example.com/advisory"],
            "cve": "CVE-2021-1234",
            "cwe": "CWE-79",
            "cvss_score": 7.5,
            "cvss_vector": "AV:N/AC:L",
            "extracted_results": ["admin"],
        }
        finding = normalize_nuclei(nf, scan_id="scan-001")
        assert finding.title == "Test Vulnerability"
        assert finding.severity == Severity.HIGH.value
        assert finding.confidence == Confidence.HIGH.value
        assert finding.source == "nuclei"
        assert finding.template_id == "CVE-2021-1234"
        assert finding.cve == "CVE-2021-1234"
        assert finding.cwe == "CWE-79"
        assert finding.cvss_score == 7.5
        assert finding.affected_asset == "https://10.10.20.15/"
        evidence = json.loads(finding.evidence)
        assert evidence["tool"] == "nuclei"
        assert evidence["template_id"] == "CVE-2021-1234"

    def test_malformed_nuclei_finding(self):
        nf = {"template_id": "", "severity": ""}
        finding = normalize_nuclei(nf, scan_id="scan-001")
        assert finding.title == "Nuclei finding"
        assert finding.severity == Severity.INFO.value
        assert finding.confidence == Confidence.UNKNOWN.value

    def test_severity_and_confidence_separate(self):
        """Severity HIGH with Confidence LOW is valid."""
        nf = {
            "template_id": "test",
            "template_name": "Test",
            "severity": "HIGH",
            "confidence": "low",
            "host": "10.10.20.15",
            "url": "http://10.10.20.15/",
        }
        finding = normalize_nuclei(nf, scan_id="scan-001")
        assert finding.severity == Severity.HIGH.value
        assert finding.confidence == Confidence.LOW.value
        assert finding.source_severity == "HIGH"


class TestExposureNormalization:
    def test_exposure_finding(self):
        finding = normalize_exposure(
            title="Redis exposed",
            description="Redis without auth",
            source="exposure-check",
            affected_asset="10.10.20.15:6379",
            severity=Severity.HIGH,
            confidence=Confidence.HIGH,
            evidence={"port": 6379},
            remediation="Restrict access",
            scan_id="scan-001",
        )
        assert finding.title == "Redis exposed"
        assert finding.severity == Severity.HIGH.value
        assert finding.source == "exposure-check"
        assert finding.affected_asset == "10.10.20.15:6379"


class TestDeduplication:
    def test_duplicate_findings_merge(self):
        key = make_dedup_key("nuclei", "CVE-2021-1234", "https://10.10.20.15/", "Test")
        f1 = Finding(dedup_key=key, title="Test", severity=Severity.HIGH.value, source="nuclei")
        f2 = Finding(dedup_key=key, title="Test", severity=Severity.MEDIUM.value, source="nuclei")
        result = deduplicate_findings([f1, f2])
        assert len(result) == 1
        # Higher severity should win
        assert result[0].severity == Severity.HIGH.value

    def test_different_findings_not_merged(self):
        f1 = Finding(dedup_key="key1", title="A", severity=Severity.HIGH.value, source="nuclei")
        f2 = Finding(dedup_key="key2", title="B", severity=Severity.LOW.value, source="nuclei")
        result = deduplicate_findings([f1, f2])
        assert len(result) == 2

    def test_dedup_key_stable(self):
        k1 = make_dedup_key("nuclei", "tpl-1", "10.10.20.15:443", "SQL Injection")
        k2 = make_dedup_key("nuclei", "tpl-1", "10.10.20.15:443", "SQL Injection")
        assert k1 == k2

    def test_dedup_key_different_for_different_assets(self):
        k1 = make_dedup_key("nuclei", "tpl-1", "10.10.20.15:443", "SQLi")
        k2 = make_dedup_key("nuclei", "tpl-1", "10.10.20.16:443", "SQLi")
        assert k1 != k2
