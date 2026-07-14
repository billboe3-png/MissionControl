"""Mission Control Agent - Entry point."""

import argparse
import asyncio
import sys

from agent.agent import MissionControlAgent
from agent.config import load_config
from agent.logger import setup_logging


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Mission Control Agent",
        prog="mc-agent",
    )
    parser.add_argument(
        "--server",
        type=str,
        help="Mission Control server URL",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        help="API key for authentication",
    )
    parser.add_argument(
        "--agent-id",
        type=int,
        help="Agent ID (from registration)",
    )
    parser.add_argument(
        "--name",
        type=str,
        help="Agent display name",
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Path to config file",
    )
    parser.add_argument(
        "--heartbeat-interval",
        type=int,
        help="Seconds between heartbeats",
    )
    parser.add_argument(
        "--no-ssl-verify",
        action="store_true",
        help="Disable SSL certificate verification",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Log level",
    )
    parser.add_argument(
        "--log-file",
        type=str,
        help="Log file path",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 1.0.0",
    )
    return parser.parse_args()


def main() -> None:
    """Main entry point."""
    args = parse_args()

    config_kwargs = {}
    if args.server:
        config_kwargs["server_url"] = args.server
    if args.api_key:
        config_kwargs["api_key"] = args.api_key
    if args.agent_id:
        config_kwargs["agent_id"] = args.agent_id
    if args.name:
        config_kwargs["agent_name"] = args.name
    if args.heartbeat_interval:
        config_kwargs["heartbeat_interval"] = args.heartbeat_interval
    if args.no_ssl_verify:
        config_kwargs["verify_ssl"] = False

    config = load_config(args.config)

    for key, value in config_kwargs.items():
        if value is not None:
            setattr(config, key, value)

    setup_logging(
        level=args.log_level or config.log_level,
        log_file=args.log_file or config.log_file,
    )

    agent = MissionControlAgent(config)

    try:
        asyncio.run(agent.start())
    except KeyboardInterrupt:
        print("\nAgent shutting down...")
        asyncio.run(agent.stop())
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
