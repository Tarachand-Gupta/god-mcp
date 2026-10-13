"""Check real Pi/Codex clients with isolated configuration; no model calls or user config writes."""

import asyncio
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from god_mcp.agents import AgentRegistry
from god_mcp.models import ServerSpec, ToolSpec
from god_mcp.server_creator import ServerCreator


def run(argv, cwd, env):
    result = subprocess.run(argv, cwd=cwd, env=env, capture_output=True, text=True, timeout=60)
    if result.returncode:
        raise RuntimeError(f"{argv[0]} exited {result.returncode}: {result.stderr[-1500:]}")
    return result.stdout


async def codex_probe(root, env):
    proc = await asyncio.create_subprocess_exec(
        "codex",
        "app-server",
        "--stdio",
        cwd=root,
        env=env,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
    )

    async def request(id, method, params):
        proc.stdin.write(
            (json.dumps({"id": id, "method": method, "params": params}) + "\n").encode()
        )
        await proc.stdin.drain()

        async def receive():
            while True:
                line = await proc.stdout.readline()
                if not line:
                    raise RuntimeError("Codex app server closed before replying")
                response = json.loads(line)
                if response.get("id") == id:
                    if "error" in response:
                        raise RuntimeError(str(response["error"]))
                    return response["result"]

        return await asyncio.wait_for(receive(), 30)

    try:
        await request(1, "initialize", {"clientInfo": {"name": "god-mcp-smoke", "version": "1"}})
        proc.stdin.write(b'{"method":"initialized"}\n')
        await proc.stdin.drain()
        result = await request(2, "mcpServerStatus/list", {"serverName": "calculator"})
        entry = next(item for item in result["data"] if item["name"] == "calculator")
        assert entry["tools"] and not entry.get("toolsError"), entry
        print("Codex native app server: connected and discovered generated calculator tools.")
    finally:
        proc.terminate()
        try:
            await asyncio.wait_for(proc.wait(), 5)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()


def main():
    repo = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix="god-mcp-harness-") as directory:
        root = Path(directory)
        r = AgentRegistry(root, root / "home", {})
        config = {
            "command": sys.executable,
            "args": ["-m", "god_mcp.server"],
            "env": {
                "PYTHONPATH": str(repo / "src"),
                "GOD_MCP_AGENT": "pi",
                "GOD_MCP_WORKSPACE": str(root),
            },
        }
        created = ServerCreator(root).create_server(
            ServerSpec(
                "smoke-calculator",
                "Smoke calculator",
                [
                    ToolSpec(
                        "add",
                        "Add two numbers",
                        {
                            "type": "object",
                            "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
                            "required": ["a", "b"],
                        },
                        implementation_hint="return {'result': a + b}",
                    )
                ],
            ),
            register=False,
        )
        assert created["success"], created
        generated = {"command": sys.executable, "args": [created["files"]["server"]]}
        assert r.install("god-mcp-smoke", config, ["pi", "codex"], "user", False)["success"]
        assert r.install("calculator", generated, ["pi", "codex"], "user", False)["success"]
        env = {
            **os.environ,
            "CODEX_HOME": str(root / "home/.codex"),
            "PI_CODING_AGENT_DIR": str(root / "home/.pi/agent"),
        }
        codex = json.loads(run(["codex", "mcp", "get", "calculator", "--json"], root, env))
        assert codex["transport"]["command"] == sys.executable, codex
        print("Codex: generated server configuration accepted (not a model invocation).")
        asyncio.run(codex_probe(root, env))
        pi = json.loads(run(["pi", "mcp", "list", "--json"], root, env))
        (root / "pi-result.json").write_text(json.dumps(pi))
        print("Pi: native CLI connected to God MCP and generated calculator.")
        # Use the actual MCP client library shipped with the installed Pi agent.
        pi_root = Path(shutil.which("pi")).resolve().parents[2]
        module = pi_root / "node_modules/@earendil-works/pi-mcp/dist/index.js"
        if not module.exists():
            raise RuntimeError(
                "Cannot locate installed Pi MCP client; set up the tested Pi distribution"
            )
        script = root / "call.mjs"
        script.write_text(
            """import { McpClient, StdioTransport } from """
            + json.dumps(module.as_uri())
            + """;
const config = """
            + json.dumps(generated)
            + """;
const client = new McpClient({name: "god-mcp-smoke", version: "1", requestTimeoutMs: 10000});
try {
  await client.connect(new StdioTransport(config));
  const tools = await client.listTools();
  if (!tools.some(t => t.name === "add")) throw new Error("add missing");
  const result = await client.callTool("add", {a:19,b:23});
  if (result.isError || !JSON.stringify(result).includes('42')) throw new Error("wrong result");
  console.log("Pi MCP client: add(19,23) returned 42.");
} finally { await client.close(); }
"""
        )
        print(run(["node", str(script)], root, env).strip())


if __name__ == "__main__":
    main()
