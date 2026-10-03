"""Tests for the Scope Manager — the central safety gate."""
import pytest

from app.scope import Scope, ScopeError, ScopeManager


class TestScopeParsing:
    def test_valid_cidr(self):
        sm = ScopeManager()
        scope = sm.parse("10.10.20.0/24")
        assert "10.10.20.0/24" in scope.cidr_list
        assert scope.address_count == 256

    def test_single_ip(self):
        sm = ScopeManager()
        scope = sm.parse("10.10.20.15")
        assert "10.10.20.15/32" in scope.cidr_list
        assert scope.address_count == 1

    def test_multiple_cidrs(self):
        sm = ScopeManager()
        scope = sm.parse("10.10.20.0/24\n10.10.30.0/24")
        assert len(scope.networks) == 2
        assert scope.address_count == 512

    def test_comma_separated(self):
        sm = ScopeManager()
        scope = sm.parse("10.10.20.0/24, 10.10.30.0/24")
        assert len(scope.networks) == 2

    def test_ip_range(self):
        sm = ScopeManager()
        scope = sm.parse("10.10.20.10-10.10.20.20")
        assert scope.address_count == 11

    def test_ipv6_enabled(self):
        sm = ScopeManager(enable_ipv6=True)
        scope = sm.parse("2001:db8::/64")
        assert len(scope.networks) == 1
        assert scope.networks[0].version == 6

    def test_ipv6_disabled_by_default(self):
        sm = ScopeManager(enable_ipv6=False)
        with pytest.raises(ScopeError, match="IPv6"):
            sm.parse("2001:db8::/64")

    def test_empty_scope_rejected(self):
        sm = ScopeManager()
        with pytest.raises(ScopeError, match="Empty scope"):
            sm.parse("")

    def test_empty_scope_with_whitespace_rejected(self):
        sm = ScopeManager()
        with pytest.raises(ScopeError, match="Empty scope"):
            sm.parse("   \n   \n")

    def test_invalid_cidr_rejected(self):
        sm = ScopeManager()
        with pytest.raises(ScopeError, match="Invalid"):
            sm.parse("not-an-ip")

    def test_invalid_range_rejected(self):
        sm = ScopeManager()
        with pytest.raises(ScopeError, match="end is before start"):
            sm.parse("10.10.20.10-10.10.20.5")

    def test_mixed_version_range_rejected(self):
        sm = ScopeManager(enable_ipv6=True)
        with pytest.raises(ScopeError, match="mixes IPv4 and IPv6"):
            sm.parse("10.10.20.10-2001:db8::1")


class TestScopeSafety:
    def test_loopback_rejected(self):
        sm = ScopeManager()
        with pytest.raises(ScopeError, match="blocked infrastructure"):
            sm.parse("127.0.0.0/8")

    def test_tailscale_cgnat_rejected(self):
        sm = ScopeManager()
        with pytest.raises(ScopeError, match="blocked infrastructure"):
            sm.parse("100.64.0.0/10")

    def test_link_local_rejected(self):
        sm = ScopeManager()
        with pytest.raises(ScopeError, match="blocked infrastructure"):
            sm.parse("169.254.0.0/16")

    def test_multicast_rejected(self):
        sm = ScopeManager()
        with pytest.raises(ScopeError, match="blocked infrastructure"):
            sm.parse("224.0.0.0/4")

    def test_too_broad_ipv4_rejected(self):
        sm = ScopeManager()
        with pytest.raises(ScopeError, match="too broad"):
            sm.parse("10.0.0.0/8")

    def test_too_broad_ipv6_rejected(self):
        sm = ScopeManager(enable_ipv6=True)
        with pytest.raises(ScopeError, match="too broad"):
            sm.parse("2001:db8::/32")

    def test_max_addresses_exceeded(self):
        sm = ScopeManager(max_addresses=100)
        with pytest.raises(ScopeError, match="exceeding the maximum"):
            sm.parse("10.10.20.0/24")


class TestScopeEnforcement:
    def test_is_in_scope_true(self):
        sm = ScopeManager()
        scope = sm.parse("10.10.20.0/24")
        assert sm.is_in_scope(scope, "10.10.20.15") is True
        assert sm.is_in_scope(scope, "10.10.20.255") is True

    def test_is_in_scope_false(self):
        sm = ScopeManager()
        scope = sm.parse("10.10.20.0/24")
        assert sm.is_in_scope(scope, "10.10.21.1") is False
        assert sm.is_in_scope(scope, "192.168.1.1") is False

    def test_assert_in_scope_raises(self):
        sm = ScopeManager()
        scope = sm.parse("10.10.20.0/24")
        with pytest.raises(ScopeError, match="outside the authorised scope"):
            sm.assert_in_scope(scope, "10.10.30.1")

    def test_assert_in_scope_passes(self):
        sm = ScopeManager()
        scope = sm.parse("10.10.20.0/24")
        sm.assert_in_scope(scope, "10.10.20.1")  # should not raise

    def test_non_ip_target_rejected(self):
        sm = ScopeManager()
        scope = sm.parse("10.10.20.0/24")
        assert sm.is_in_scope(scope, "example.com") is False

    def test_filter_targets(self):
        sm = ScopeManager()
        scope = sm.parse("10.10.20.0/24")
        targets = ["10.10.20.1", "10.10.20.2", "10.10.30.1", "192.168.1.1"]
        filtered = sm.filter_targets(scope, targets)
        assert "10.10.20.1" in filtered
        assert "10.10.20.2" in filtered
        assert "10.10.30.1" not in filtered
        assert "192.168.1.1" not in filtered


class TestScopeOverlap:
    def test_overlapping_ranges_collapse(self):
        sm = ScopeManager()
        scope = sm.parse("10.10.20.0/24\n10.10.20.128/25")
        assert len(scope.networks) == 1
        assert scope.address_count == 256

    def test_adjacent_ranges_merge(self):
        sm = ScopeManager()
        scope = sm.parse("10.10.20.0/25\n10.10.20.128/25")
        assert len(scope.networks) == 1
        assert scope.address_count == 256


class TestScopeSerialization:
    def test_to_json_and_back(self):
        sm = ScopeManager()
        scope = sm.parse("10.10.20.0/24", name="test scope")
        j = scope.to_json()
        scope2 = Scope.from_json(j)
        assert scope2.name == "test scope"
        assert scope2.cidr_list == scope.cidr_list
        assert scope2.address_count == scope.address_count
