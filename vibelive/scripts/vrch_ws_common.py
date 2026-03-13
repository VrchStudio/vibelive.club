#!/usr/bin/env python3
"""Shared helpers for the vibelive skill."""

from __future__ import annotations

import json
import time
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "assets" / "vrch_08_party.json"


@dataclass(frozen=True)
class ImageFrame:
    raw_type: int
    batch_id: int
    frame_index: int
    frame_total: int
    image_bytes: bytes


def load_event_config(config_path: str | None = None) -> dict[str, Any]:
    path = Path(config_path).expanduser().resolve() if config_path else DEFAULT_CONFIG_PATH
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def normalize_ws_base_url(value: str) -> str:
    text = value.strip()
    if not text:
        raise ValueError("WebSocket server address is empty.")

    if "://" not in text:
        text = f"ws://{text}"

    parsed = urllib.parse.urlparse(text)
    scheme = parsed.scheme.lower()
    if scheme == "http":
        scheme = "ws"
    elif scheme == "https":
        scheme = "wss"
    elif scheme not in {"ws", "wss"}:
        raise ValueError(f"Unsupported scheme: {parsed.scheme}")

    netloc = parsed.netloc or parsed.path
    path = parsed.path if parsed.netloc else ""
    normalized = urllib.parse.urlunparse((scheme, netloc, path.rstrip("/"), "", "", ""))
    return normalized.rstrip("/")


def build_ws_url(base_url: str, endpoint: str, channel: int) -> str:
    base = normalize_ws_base_url(base_url)
    endpoint = endpoint.strip().lstrip("/")
    return f"{base}/{endpoint}?channel={int(channel)}"


def get_default_channel(config: dict[str, Any], key: str) -> int:
    channels = config.get("channels", {})
    value = channels.get(key)
    if value is None:
        raise KeyError(f"Missing channel '{key}' in event config.")
    return int(value)


def get_default_prompt_settings(config: dict[str, Any]) -> tuple[bool, str]:
    prompt_defaults = config.get("prompt_defaults", {})
    ai_enhancement = bool(prompt_defaults.get("ai_enhancement", True))
    style = str(prompt_defaults.get("style", "base")).strip() or "base"
    return ai_enhancement, style


def parse_image_frame(message: bytes | bytearray | memoryview) -> ImageFrame:
    payload = bytes(message)
    if len(payload) < 8:
        raise ValueError("Image payload is shorter than the 8-byte VRCH header.")

    raw_type = int.from_bytes(payload[0:4], byteorder="big", signed=False)
    meta = int.from_bytes(payload[4:8], byteorder="big", signed=False)
    batch_id = (meta >> 16) & 0xFFFF
    frame_index = (meta >> 8) & 0xFF
    frame_total = meta & 0xFF

    return ImageFrame(
        raw_type=raw_type,
        batch_id=batch_id,
        frame_index=frame_index,
        frame_total=frame_total,
        image_bytes=payload[8:],
    )


def make_prompt_payload(prompt: str, ai_enhancement: bool, style: str) -> str:
    data = {
        "prompt": prompt,
        "ai_enhancement": bool(ai_enhancement),
        "style": style,
    }
    return json.dumps(data, ensure_ascii=False)


def make_live_console_payload(ops: list[dict[str, Any]], source: str = "vibelive-skill") -> str:
    now_ms = int(time.time() * 1000)
    data = {
        "live_console_control": {
            "version": "1.0",
            "request_id": f"lc-{now_ms}",
            "timestamp_ms": now_ms,
            "ops": ops,
            "meta": {
                "source": source,
            },
        }
    }
    return json.dumps(data, ensure_ascii=False)
