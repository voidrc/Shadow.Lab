"""Tests for the Executor abstraction and pre-flight checks."""
import shutil
from unittest.mock import patch

import pytest

from app.executor import LocalExecutor, SSHExecutor, RunResult
from app.preflight import preflight, check_local, PROFILE_TOOLS


class TestLocalExecutor:
    def test_run_success(self):
        ex = LocalExecutor()
        result = ex.run("echo", ["echo", "hello"], timeout=5)
        assert result.returncode == 0
        assert "hello" in result.stdout
        assert result.ok

    def test_run_failure(self):
        ex = LocalExecutor()
        result = ex.run("false", ["false"], timeout=5)
        assert result.returncode != 0
        assert not result.ok

    def test_run_not_found(self):
        ex = LocalExecutor()
        result = ex.run("nonexistent-tool-xyz", ["nonexistent-tool-xyz"], timeout=5)
        assert result.returncode == 127
        assert not result.ok

    def test_run_with_stdin(self):
        ex = LocalExecutor()
        result = ex.run("cat", ["cat"], stdin="hello via stdin", timeout=5)
        assert result.returncode == 0
        assert "hello via stdin" in result.stdout

    def test_build_command_passthrough(self):
        ex = LocalExecutor()
        cmd = ex.build_command(["nmap", "-sn", "10.10.20.0/24"])
        assert cmd == ["nmap", "-sn", "10.10.20.0/24"]


class TestSSHExecutor:
    def test_build_command_wraps_with_tailscale_ssh(self):
        ex = SSHExecutor(host="medusa")
        cmd = ex.build_command(["nmap", "-sn", "10.10.20.0/24"])
        assert cmd[0] == "tailscale" or cmd[0].endswith("tailscale")
        assert "ssh" in cmd
        assert "medusa" in cmd
        assert "nmap" in cmd

    def test_build_command_with_user(self):
        ex = SSHExecutor(host="medusa", user="analyst")
        cmd = ex.build_command(["nmap"])
        assert "analyst@medusa" in cmd

    def test_target_property(self):
        ex = SSHExecutor(host="medusa")
        assert ex.target == "medusa"
        ex2 = SSHExecutor(host="medusa", user="analyst")
        assert ex2.target == "analyst@medusa"

    def test_check_tool_returns_true_when_found(self):
        ex = SSHExecutor(host="medusa")
        # Mock the run method to simulate finding nmap
        with patch.object(ex, "run", return_value=RunResult(
            "preflight", ["command", "-v", "nmap"], 0, "/usr/bin/nmap\n", "", 0.1
        )):
            assert ex.check_tool("nmap") is True

    def test_check_tool_returns_false_when_missing(self):
        ex = SSHExecutor(host="medusa")
        with patch.object(ex, "run", return_value=RunResult(
            "preflight", ["command", "-v", "httpx"], 1, "", "not found", 0.1
        )):
            assert ex.check_tool("httpx") is False


class TestPreflight:
    def test_check_local_finds_echo(self):
        # echo is always available
        result = check_local(["echo"])
        assert result.ok
        assert "echo" in result.available
        assert result.missing == []

    def test_check_local_finds_missing(self):
        result = check_local(["nonexistent-tool-xyz"])
        assert not result.ok
        assert "nonexistent-tool-xyz" in result.missing

    def test_preflight_local(self):
        result = preflight("local", "safe")
        assert result.worker == "local"
        # nmap might not be installed locally — that's fine, we're testing the logic
        assert isinstance(result.ok, bool)
        assert isinstance(result.missing, list)
        assert isinstance(result.available, list)

    def test_preflight_remote_with_mock(self):
        # Mock SSHExecutor.check_tool to simulate all tools present
        with patch("app.preflight.SSHExecutor") as MockSSH:
            instance = MockSSH.return_value
            instance.host = "medusa"
            instance.check_tool.return_value = True
            result = preflight("medusa", "safe")
            assert result.ok
            assert result.worker == "medusa"
            assert len(result.available) == len(PROFILE_TOOLS["safe"])

    def test_preflight_remote_missing_tools_with_mock(self):
        with patch("app.preflight.SSHExecutor") as MockSSH:
            instance = MockSSH.return_value
            instance.host = "medusa"
            # Simulate nmap present, httpx missing
            def check_side_effect(tool):
                return tool == "nmap"
            instance.check_tool.side_effect = check_side_effect
            result = preflight("medusa", "safe")
            assert not result.ok
            assert "nmap" in result.available
            assert "httpx" in result.missing
            assert any("pacman" in inst for inst in result.instructions)

    def test_profile_tools_recon_excludes_nuclei(self):
        assert "nuclei" not in PROFILE_TOOLS["recon"]
        assert "nmap" in PROFILE_TOOLS["recon"]
