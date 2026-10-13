import os
from pathlib import Path
import sys
import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from god_mcp.models import ServerSpec, ToolSpec
from god_mcp.server_creator import ServerCreator


@pytest.mark.asyncio
async def test_generated_server_real_tool_call(tmp_path):
    tool = ToolSpec('add', 'Add "numbers" safely', {"type": "object", "properties": {"optional": {"type": "string"}, "a": {"type": "integer"}, "b": {"type": "integer"}}, "required": ["a", "b"]}, implementation_hint='return {"result": a + b}')
    creator = ServerCreator(tmp_path)
    spec = ServerSpec('calculator', 'Quotes " and newlines\nare valid', [tool])
    result = creator.create_server(spec, register=False)
    assert result['success'], result
    assert not creator.create_server(spec, register=False)['success']
    params = StdioServerParameters(command=sys.executable, args=[result['files']['server']])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            listing = await session.list_tools()
            assert 'add' in [t.name for t in listing.tools]
            response = await session.call_tool('add', {'a': 19, 'b': 23})
            assert not response.isError
            assert '42' in response.content[0].text


@pytest.mark.asyncio
async def test_module_entrypoint_registers_all_tools(tmp_path):
    env = {**os.environ, "GOD_MCP_WORKSPACE": str(tmp_path), "GOD_MCP_AGENT": "codex"}
    params = StdioServerParameters(command=sys.executable, args=['-m', 'god_mcp.server'], env=env)
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            names = {t.name for t in (await session.list_tools()).tools}
            assert {'create_mcp_server', 'install_mcp_server', 'discover_agents', 'health_check'} <= names
            response = await session.call_tool('health_check', {})
            assert not response.isError
            result = await session.call_tool('create_mcp_server', {'name':'through-mcp', 'description':'test', 'output_dir':str(tmp_path), 'register':False, 'tools':[{'name':'ping','description':'Ping','parameters':{'type':'object'},'implementation':'return "pong"'}]})
            assert not result.isError
            assert (tmp_path / 'through-mcp/src/through_mcp/server.py').exists()


def test_invalid_code_does_not_create_package(tmp_path):
    spec = ServerSpec('bad-code', 'Invalid', [ToolSpec('run', 'Run', {}, implementation_hint='return (')])
    assert not ServerCreator(tmp_path).create_server(spec, register=False)['success']
    assert not (tmp_path / 'bad-code').exists()


def test_registration_failure_preserves_generated_package(tmp_path, monkeypatch):
    for key in ('GOD_MCP_AGENT', 'CODEX_THREAD_ID', 'CODEX_SESSION_ID', 'CLAUDECODE', 'WORKSPACE_MCP_CONFIG_PATH', 'USER_MCP_CONFIG_PATH'):
        monkeypatch.delenv(key, raising=False)
    spec = ServerSpec('generated-only', 'Generated', [ToolSpec('run', 'Run', {}, implementation_hint='return "ok"')])
    result = ServerCreator(tmp_path).create_server(spec)
    assert result['success'] and result['registered'] is False
    assert Path(result['files']['server']).exists()
