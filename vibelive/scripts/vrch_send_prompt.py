#!/usr/bin/env python3
"""Send a prompt payload to the VRCH /json websocket channel used by Prompt Sender."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

from vrch_ws_common import (
    build_ws_url,
    get_default_channel,
    get_default_prompt_settings,
    load_event_config,
    make_prompt_payload,
)


async def send_prompt(ws_url: str, payload: str) -> None:
    try:
        import websockets
    except ImportError as exc:  # pragma: no cover - runtime dependency
        raise SystemExit(
            "Missing dependency 'websockets'. Install with: "
            "python3 -m pip install -r vibelive/scripts/requirements.txt"
        ) from exc

    async with websockets.connect(ws_url, max_size=None, ping_interval=20, ping_timeout=20) as websocket:
        await websocket.send(payload)
        await asyncio.sleep(0.15)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", help="Path to event config JSON.")
    parser.add_argument("--server", help="WebSocket base URL. Example: wss://vrch-08.vrch.ai/vrch-ws/")
    parser.add_argument("--channel", type=int, help="Prompt websocket channel. Defaults to the event config value.")
    parser.add_argument("--prompt", required=True, help="Prompt text. Use '-' to read from stdin.")
    parser.add_argument("--style", help="Prompt style code. Defaults to the event config value.")
    parser.add_argument(
        "--ai-enhancement",
        dest="ai_enhancement",
        action="store_true",
        help="Enable AI enhancement in the payload.",
    )
    parser.add_argument(
        "--no-ai-enhancement",
        dest="ai_enhancement",
        action="store_false",
        help="Disable AI enhancement in the payload.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print the payload but do not send it.")
    parser.set_defaults(ai_enhancement=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_event_config(args.config)
    default_ai, default_style = get_default_prompt_settings(config)

    server = args.server or config["ws_base_url"]
    channel = args.channel if args.channel is not None else get_default_channel(config, "prompt")
    style = (args.style or default_style).strip() or "base"
    ai_enhancement = default_ai if args.ai_enhancement is None else bool(args.ai_enhancement)
    prompt = sys.stdin.read().strip() if args.prompt == "-" else args.prompt.strip()
    if not prompt:
        raise SystemExit("Prompt text is empty.")

    ws_url = build_ws_url(server, "json", channel)
    payload = make_prompt_payload(prompt=prompt, ai_enhancement=ai_enhancement, style=style)

    if not args.dry_run:
        asyncio.run(send_prompt(ws_url, payload))

    result = {
        "event_name": config.get("event_name"),
        "host_id": config.get("host_id"),
        "console_url": config.get("console_url"),
        "ws_url": ws_url,
        "channel": channel,
        "payload": json.loads(payload),
        "sent": not args.dry_run,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
