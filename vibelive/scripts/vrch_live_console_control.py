#!/usr/bin/env python3
"""Show or hide panes in VRCH Live Console through the /json control channel."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

from vrch_ws_common import build_ws_url, load_event_config, make_live_console_payload


KNOWN_PANES = {
    "viewer",
    "viewerAux",
    "settings",
    "prompt",
    "srt",
    "sketch",
    "image",
    "audioRecorder",
    "audioPlayer",
    "midi",
    "gamepad",
}

PRESETS = {
    "vibe_agent": {
        "viewer": True,
        "viewerAux": False,
        "settings": True,
        "prompt": True,
        "srt": False,
        "sketch": False,
        "image": True,
        "audioRecorder": False,
        "audioPlayer": False,
        "midi": False,
        "gamepad": False,
    }
}


async def send_payload(ws_url: str, payload: str) -> None:
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


def parse_pane_csv(value: str | None) -> list[str]:
    if not value:
        return []
    items = [item.strip() for item in value.split(",") if item.strip()]
    invalid = [item for item in items if item not in KNOWN_PANES]
    if invalid:
        raise SystemExit(f"Unknown pane ids: {', '.join(invalid)}")
    return items


def build_ops(show: list[str], hide: list[str], preset: str | None) -> list[dict[str, object]]:
    states: dict[str, bool] = {}
    if preset:
        states.update(PRESETS[preset])
    for pane in show:
        states[pane] = True
    for pane in hide:
        states[pane] = False
    if not states:
        raise SystemExit("No pane operations requested. Use --preset, --show, or --hide.")

    return [
        {
            "op": "pane.set_visibility",
            "target": pane,
            "args": {"visible": visible},
        }
        for pane, visible in states.items()
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", help="Path to event config JSON.")
    parser.add_argument("--server", help="WebSocket base URL. Example: wss://vrch-08.vrch.ai/vrch-ws/")
    parser.add_argument(
        "--channel",
        type=int,
        help="Live console control channel. Defaults to the event config value.",
    )
    parser.add_argument("--preset", choices=sorted(PRESETS), help="Apply a predefined pane visibility layout.")
    parser.add_argument("--show", help="Comma-separated pane ids to show.")
    parser.add_argument("--hide", help="Comma-separated pane ids to hide.")
    parser.add_argument("--dry-run", action="store_true", help="Print the payload but do not send it.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_event_config(args.config)
    server = args.server or config["ws_base_url"]
    channel = int(args.channel or config["channels"]["status_workflow_console"])
    show = parse_pane_csv(args.show)
    hide = parse_pane_csv(args.hide)
    ops = build_ops(show=show, hide=hide, preset=args.preset)
    payload = make_live_console_payload(ops)
    ws_url = build_ws_url(server, "json", channel)

    if not args.dry_run:
        asyncio.run(send_payload(ws_url, payload))

    result = {
        "event_name": config.get("event_name"),
        "host_id": config.get("host_id"),
        "console_url": config.get("console_url"),
        "ws_url": ws_url,
        "channel": channel,
        "ops": json.loads(payload)["live_console_control"]["ops"],
        "sent": not args.dry_run,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
