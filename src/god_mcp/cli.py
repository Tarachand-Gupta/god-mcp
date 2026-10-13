"""Headless agent discovery and MCP registration without starting a model."""

import argparse
import json
from pathlib import Path
from god_mcp.agents import AgentRegistry


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", default=".")
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("agents")
    for action in ("install", "bootstrap"):
        cmd = sub.add_parser(action)
        cmd.add_argument(
            "--target",
            action="append",
            help="Agent ID, current, detected or all; repeat for multiple targets",
        )
        cmd.add_argument("--scope", choices=["workspace", "user"], default="workspace")
        cmd.add_argument("--apply", action="store_true", help="Write configs; otherwise preview")
        cmd.add_argument(
            "--replace", action="store_true", help="Intentionally replace a conflicting named entry"
        )
        if action == "install":
            cmd.add_argument("name")
            cmd.add_argument(
                "--config",
                required=True,
                help="JSON file containing one command/args or url server entry",
            )
    args = parser.parse_args()
    registry = AgentRegistry(args.workspace)
    try:
        if args.action == "agents":
            result = {"current": registry.current(), "agents": registry.discover()}
        elif args.action == "install":
            result = registry.install(
                args.name,
                json.loads(Path(args.config).read_text()),
                args.target,
                args.scope,
                not args.apply,
                args.replace,
            )
        else:
            # Each host gets its identity explicitly; do not infer from the selected model.
            results = []
            root = str(Path(__file__).resolve().parents[2])
            for target in registry.targets(args.target):
                config = {
                    "command": "uv",
                    "args": ["run", "--directory", root, "god-mcp"],
                    "env": {"GOD_MCP_AGENT": target, "GOD_MCP_WORKSPACE": str(registry.workspace)},
                }
                item = registry.install(
                    "god-mcp", config, [target], args.scope, not args.apply, args.replace
                )
                results.extend(item["results"])
            result = {
                "success": bool(results) and all(r["status"] != "error" for r in results),
                "results": results,
            }
        print(json.dumps(result, indent=2))
        if result.get("success") is False:
            raise SystemExit(1)
    except (ValueError, OSError) as exc:
        print(json.dumps({"success": False, "error": str(exc)}))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
