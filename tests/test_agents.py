import json
from pathlib import Path
import pytest
import tomlkit
from god_mcp.agents import AgentRegistry, write_entry


def registry(tmp_path, env=None):
    return AgentRegistry(tmp_path / "project", tmp_path / "home", env or {})


def test_current_is_not_installed(tmp_path):
    r = registry(tmp_path)
    with pytest.raises(ValueError, match="unknown"):
        r.targets(["current"])
    assert r.targets(["pi", "codex", "pi"]) == ["pi", "codex"]
    assert registry(tmp_path, {"GOD_MCP_AGENT": "pi"}).current() == "pi"
    assert registry(tmp_path, {"CODEX_THREAD_ID": "test", "CLAUDECODE": "1"}).current() is None


def test_json_and_toml_preserve_backup_and_idempotence(tmp_path):
    r = registry(tmp_path)
    path = r.path("codex", "user")
    path.parent.mkdir(parents=True)
    original = '# keep my comment\nmodel = "test"\n[mcp_servers.existing]\ncommand = "example"\n'
    path.write_text(original)
    config = {"command": "python", "args": ["a path with spaces.py"]}
    assert r.install("demo", config, ["codex"], "user")["results"][0]["status"] == "planned"
    assert path.read_text() == original
    applied = r.install("demo", config, ["codex", "pi"], "user", False)
    assert applied["success"]
    assert '# keep my comment' in path.read_text()
    assert tomlkit.parse(path.read_text())["mcp_servers"]["existing"]["command"] == "example"
    assert Path(applied["results"][0]["backup"]).read_text() == original
    assert json.loads(r.path("pi", "user").read_text())["mcpServers"]["demo"] == config
    assert r.install("demo", config, ["codex"], "user", False)["results"][0]["status"] == "unchanged"
    assert not r.install("demo", {"command": "other"}, ["codex"], "user", False)["success"]


def test_invalid_file_not_overwritten(tmp_path):
    path = tmp_path / "mcp.json"
    path.write_text('{invalid')
    with pytest.raises(ValueError):
        write_entry(path, "mcpServers", "test", {"command": "test"}, dry_run=False)
    assert path.read_text() == '{invalid'


def test_all_includes_undetected_and_custom(tmp_path):
    custom = tmp_path / "agents.json"
    custom.write_text(json.dumps([{"id": "new-agent", "user_path": "~/.new/mcp.json", "workspace_path": ".new/mcp.json", "key": "servers"}]))
    r = AgentRegistry(tmp_path, tmp_path / "home", {}, custom)
    assert "new-agent" in r.targets(["all"])
    result = r.install("tool", {"url": "https://example.com/mcp"}, ["new-agent"], dry_run=False)
    assert result["success"]
    assert json.loads((tmp_path / ".new/mcp.json").read_text())["servers"]["tool"]["url"].startswith("https")


def test_partial_failure_is_reported(tmp_path):
    result = registry(tmp_path).install("demo", {"command": "test"}, ["pi", "windsurf"], "workspace", False)
    assert not result["success"]
    assert [r["status"] for r in result["results"]] == ["configured", "error"]


def test_unknown_fields_are_not_silently_dropped(tmp_path):
    with pytest.raises(ValueError, match="Unsupported"):
        registry(tmp_path).install("remote", {"url": "https://example.com", "headers": {"Authorization": "placeholder"}}, ["codex"])


def test_redaction():
    from god_mcp.server import redact_config
    result = redact_config({"mcpServers": {"test": {"command": "python", "args": ["sensitive"], "env": {"KEY": "sensitive"}, "url": "https://example.com/?key=sensitive"}}})
    assert "sensitive" not in json.dumps(result)
    assert result["mcpServers"]["test"]["command"] == "python"


def test_removal_preserves_other_servers_and_backup(tmp_path):
    path = tmp_path / 'mcp.json'
    original = json.dumps({'mcpServers': {'one': {'command': 'a'}, 'two': {'command': 'b'}}, 'setting': True})
    path.write_text(original)
    result = write_entry(path, 'mcpServers', 'one', None, dry_run=False, remove=True)
    assert Path(result['backup']).read_text() == original
    assert json.loads(path.read_text()) == {'mcpServers': {'two': {'command': 'b'}}, 'setting': True}
