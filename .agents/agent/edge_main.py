"""Mission Control Edge Agent - Entry point for the new edge collector."""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

from agent.config import load_config
from agent.edge_core import EdgeCore
from agent.logger import setup_logging


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Mission Control Edge Agent",
        prog="mc-edge",
    )
    parser.add_argument("--server", type=str, help="Mission Control server URL")
    parser.add_argument("--api-key", type=str, help="API key for authentication")
    parser.add_argument("--agent-id", type=int, help="Agent ID")
    parser.add_argument("--name", type=str, help="Agent display name")
    parser.add_argument("--config", type=str, help="Path to config file")
    parser.add_argument(
        "--heartbeat-interval", type=int, help="Seconds between heartbeats"
    )
    parser.add_argument(
        "--no-ssl-verify", action="store_true", help="Disable SSL verification"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default=None,
    )
    parser.add_argument("--log-file", type=str, help="Log file path")
    parser.add_argument(
        "--version", action="version", version="%(prog)s 3.0.0-rc1-edge"
    )
    return parser.parse_args()


def _bootstrap_sys_path() -> None:
    candidates = [
        Path(__file__).resolve().parent,
        Path.cwd() / "agent",
        Path.cwd(),
    ]
    for candidate in candidates:
        if str(candidate) not in sys.path:
            sys.path.insert(0, str(candidate))


def main() -> None:
    _bootstrap_sys_path()
    args = parse_args()

    config = load_config(args.config)
    overrides = {
        "server_url": args.server,
        "api_key": args.api_key,
        "agent_id": args.agent_id,
        "agent_name": args.name,
        "heartbeat_interval": args.heartbeat_interval,
    }
    if args.no_ssl_verify:
        overrides["verify_ssl"] = False
    for key, value in overrides.items():
        if value is not None:
            setattr(config, key, value)

    setup_logging(
        level=args.log_level or config.log_level,
        log_file=args.log_file or config.log_file,
    )

    while True:
        core = EdgeCore(config)
        try:
            asyncio.run(core.start())
        except KeyboardInterrupt:
            logging.info("Edge agent stopped by user")
            break
        except Exception as e:
            logging.error("Edge agent failed: %s", e)
        if not getattr(core, "_running", False):
            logging.info("Edge agent restarting...")
            continue
        break


if __name__ == "__main__":
    main()
