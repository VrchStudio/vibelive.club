#!/usr/bin/env python3
"""Capture one live frame from a VRCH /image websocket channel."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from io import BytesIO
from pathlib import Path

from vrch_ws_common import build_ws_url, get_default_channel, load_event_config, parse_image_frame


async def capture_one_frame(ws_url: str, timeout: float) -> tuple[dict[str, object], bytes, str]:
    try:
        import websockets
    except ImportError as exc:  # pragma: no cover - runtime dependency
        raise SystemExit(
            "Missing dependency 'websockets'. Install with: "
            "python3 -m pip install -r vibelive/scripts/requirements.txt"
        ) from exc

    try:
        from PIL import Image
    except ImportError as exc:  # pragma: no cover - runtime dependency
        raise SystemExit(
            "Missing dependency 'Pillow'. Install with: "
            "python3 -m pip install -r vibelive/scripts/requirements.txt"
        ) from exc

    async with websockets.connect(ws_url, max_size=None, ping_interval=20, ping_timeout=20) as websocket:
        loop = asyncio.get_running_loop()
        deadline = loop.time() + timeout

        while True:
            remaining = deadline - loop.time()
            if remaining <= 0:
                raise TimeoutError(f"No binary image frame arrived within {timeout:.1f}s.")

            message = await asyncio.wait_for(websocket.recv(), timeout=remaining)

            if isinstance(message, str):
                continue

            frame = parse_image_frame(message)
            image = Image.open(BytesIO(frame.image_bytes))
            image.load()
            image_format = (image.format or "JPEG").upper()

            meta = {
                "raw_type": frame.raw_type,
                "batch_id": frame.batch_id,
                "frame_index": frame.frame_index,
                "frame_total": frame.frame_total,
                "width": int(image.width),
                "height": int(image.height),
                "image_format": image_format,
                "bytes": len(frame.image_bytes),
            }
            return meta, frame.image_bytes, image_format


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", help="Path to event config JSON.")
    parser.add_argument("--server", help="WebSocket base URL. Example: wss://vrch-08.vrch.ai/vrch-ws/")
    parser.add_argument("--channel", type=int, help="Image websocket channel. Defaults to the event config value.")
    parser.add_argument("--timeout", type=float, default=20.0, help="Seconds to wait for a live frame. Default: 20")
    parser.add_argument(
        "--out",
        default="vrch_latest_scene.jpg",
        help="Where to save the captured image. Default: ./vrch_latest_scene.jpg",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_event_config(args.config)
    server = args.server or config["ws_base_url"]
    channel = args.channel if args.channel is not None else get_default_channel(config, "image")
    ws_url = build_ws_url(server, "image", channel)

    output_path = Path(args.out).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    meta, image_bytes, image_format = asyncio.run(capture_one_frame(ws_url, timeout=args.timeout))
    expected_suffixes = {".png"} if image_format == "PNG" else {".jpg", ".jpeg"}
    suffix = ".png" if image_format == "PNG" else ".jpg"
    if output_path.suffix.lower() not in expected_suffixes:
        output_path = output_path.with_suffix(suffix)

    output_path.write_bytes(image_bytes)

    result = {
        "event_name": config.get("event_name"),
        "host_id": config.get("host_id"),
        "console_url": config.get("console_url"),
        "viewer_url": config.get("viewer_url"),
        "ws_url": ws_url,
        "channel": channel,
        "output_path": str(output_path),
        **meta,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
