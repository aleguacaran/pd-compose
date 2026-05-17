import subprocess
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from pd_compose.cli import app

runner = CliRunner()


@pytest.fixture
def config_file(tmp_path: Path) -> Path:
    config = {
        "services": {
            "test-vm": {
                "image": "alpine:latest",
                "binds": ["/host/path:/container/path"],
                "environment": {"FOO": "bar", "BAZ": "qux"},
            }
        }
    }
    path = tmp_path / "pd-compose.yaml"
    with open(path, "w") as f:
        yaml.dump(config, f)
    return path


def test_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "pd-compose:" in result.stdout
    assert "up" in result.stdout
    assert "down" in result.stdout
    assert "ps" in result.stdout


def test_up_help():
    result = runner.invoke(app, ["up", "--help"])
    assert result.exit_code == 0
    assert "--file" in result.stdout
    assert "--dry-run" in result.stdout


def test_down_help():
    result = runner.invoke(app, ["down", "--help"])
    assert result.exit_code == 0
    assert "--file" in result.stdout
    assert "--dry-run" in result.stdout


def test_invalid_command():
    result = runner.invoke(app, ["invalid"])
    assert result.exit_code != 0


def test_ps_no_config():
    result = runner.invoke(app, ["ps"])
    assert result.exit_code == 0


def test_up_missing_config():
    result = runner.invoke(app, ["up"])
    assert result.exit_code == 1
    assert "not found" in result.stderr


def test_down_missing_config():
    result = runner.invoke(app, ["down"])
    assert result.exit_code == 1
    assert "not found" in result.stderr


def test_up_dry_run(config_file, monkeypatch):
    calls = []
    original_run = subprocess.run

    def mock_run(*args, **kwargs):
        calls.append(args[0])
        return original_run(["echo", "mocked"])

    monkeypatch.setattr(subprocess, "run", mock_run)

    result = runner.invoke(app, ["up", "--file", str(config_file), "--dry-run"])
    assert result.exit_code == 0
    assert "Installing test-vm from alpine:latest" in result.stdout
    content = result.stdout
    assert "proot-distro login test-vm" in content
    assert "--bind /host/path:/container/path" in content
    assert "--env FOO=bar" in content
    assert "--env BAZ=qux" in content

    assert len(calls) == 0, "subprocess.run should not be called with --dry-run"


def test_down_dry_run(config_file, monkeypatch):
    calls = []

    def mock_run(*args, **kwargs):
        calls.append(args[0])
        return type("MockResult", (), {"returncode": 0})()

    monkeypatch.setattr(subprocess, "run", mock_run)

    result = runner.invoke(app, ["down", "--file", str(config_file), "--dry-run"])
    assert result.exit_code == 0
    assert "Removing test-vm" in result.stdout
    assert len(calls) == 0, "subprocess.run should not be called with --dry-run"


def test_up_with_custom_file(config_file, monkeypatch):
    calls = []

    def mock_run(*args, **kwargs):
        calls.append(args[0])
        return type("MockResult", (), {"returncode": 0})()

    monkeypatch.setattr(subprocess, "run", mock_run)

    result = runner.invoke(app, ["up", "-f", str(config_file)])
    assert result.exit_code == 0
    assert len(calls) == 1
    assert calls[0] == ["proot-distro", "install", "--name", "test-vm", "alpine:latest"]


def test_down_with_custom_file(config_file, monkeypatch):
    calls = []

    def mock_run(*args, **kwargs):
        calls.append(args[0])
        return type("MockResult", (), {"returncode": 0})()

    monkeypatch.setattr(subprocess, "run", mock_run)

    result = runner.invoke(app, ["down", "-f", str(config_file)])
    assert result.exit_code == 0
    assert len(calls) == 1
    assert calls[0] == ["proot-distro", "remove", "test-vm"]


def test_empty_services(tmp_path, monkeypatch):
    config = {"services": {}}
    path = tmp_path / "empty.yaml"
    with open(path, "w") as f:
        yaml.dump(config, f)

    calls = []

    def mock_run(*args, **kwargs):
        calls.append(args[0])
        return type("MockResult", (), {"returncode": 0})()

    monkeypatch.setattr(subprocess, "run", mock_run)

    result = runner.invoke(app, ["up", "-f", str(path)])
    assert result.exit_code == 0
    assert len(calls) == 0


def test_multiple_services(tmp_path, monkeypatch):
    config = {
        "services": {
            "web": {"image": "nginx:latest"},
            "db": {"image": "postgres:17"},
        }
    }
    path = tmp_path / "multi.yaml"
    with open(path, "w") as f:
        yaml.dump(config, f)

    calls = []

    def mock_run(*args, **kwargs):
        calls.append(args[0])
        return type("MockResult", (), {"returncode": 0})()

    monkeypatch.setattr(subprocess, "run", mock_run)

    result = runner.invoke(app, ["up", "-f", str(path)])
    assert result.exit_code == 0
    assert len(calls) == 2
    assert {"web", "db"} == {c[3] for c in calls}
    assert sorted(calls) == sorted([
        ["proot-distro", "install", "--name", "web", "nginx:latest"],
        ["proot-distro", "install", "--name", "db", "postgres:17"],
    ])


def test_default_image(tmp_path, monkeypatch):
    config = {"services": {"noimage": {}}}
    path = tmp_path / "noimage.yaml"
    with open(path, "w") as f:
        yaml.dump(config, f)

    calls = []

    def mock_run(*args, **kwargs):
        calls.append(args[0])
        return type("MockResult", (), {"returncode": 0})()

    monkeypatch.setattr(subprocess, "run", mock_run)

    result = runner.invoke(app, ["up", "-f", str(path)])
    assert result.exit_code == 0
    assert len(calls) == 1
    assert calls[0] == ["proot-distro", "install", "--name", "noimage", "ubuntu"]


def test_up_down_roundtrip(tmp_path, monkeypatch):
    config = {"services": {"rt": {"image": "busybox:latest"}}}
    path = tmp_path / "rt.yaml"
    with open(path, "w") as f:
        yaml.dump(config, f)

    calls = []

    def mock_run(*args, **kwargs):
        calls.append(args[0])

    monkeypatch.setattr(subprocess, "run", mock_run)

    result_up = runner.invoke(app, ["up", "-f", str(path)])
    assert result_up.exit_code == 0
    assert calls == [["proot-distro", "install", "--name", "rt", "busybox:latest"]]

    calls.clear()

    result_down = runner.invoke(app, ["down", "-f", str(path)])
    assert result_down.exit_code == 0
    assert calls == [["proot-distro", "remove", "rt"]]
