# VRCH Protocol Notes

Use this reference only when you need to change endpoints, channels, or debug transport issues.

## Event defaults for this skill

- Host: `vrch-08`
- Console: `https://vrch-08.vrch.ai/console`
- Viewer hub: `https://vrch-08.vrch.ai/viewer`
- WebSocket base: `wss://vrch-08.vrch.ai/vrch-ws/`
- Default channels:
  - Prompt sender: `1`
  - Image sender / camera feed: `2`
  - Live Console control: `8`

These defaults come from the bundled config file at `assets/vrch_08_party.json` and match the pane/channel defaults in `vrch_live_console.html`.

## Image sender transport

- Endpoint: `/image?channel=N`
- Sender page: `vrch_image_websocket_sender.html`
- Camera mode uses the same `/image` websocket transport as image/video/screen mode.
- Binary payload format:
  - First 8 bytes: two big-endian uint32 values.
  - First uint32: `raw_type`
  - Second uint32 packs:
    - `batch_id = (meta >> 16) & 0xFFFF`
    - `frame_index = (meta >> 8) & 0xFF`
    - `frame_total = meta & 0xFF`
  - Remaining bytes: JPEG or PNG image bytes

The current image sender page sends camera frames as `header = struct.pack(">II", 1, 2)` plus the encoded image blob.

## Prompt sender transport

- Endpoint: `/json?channel=N`
- Sender page: `vrch_prompt_websocket_sender.html`
- Payload shape:

```json
{
  "prompt": "cinematic neon crowd energy, sharp strobes, metallic reflections",
  "ai_enhancement": true,
  "style": "base"
}
```

Keep the prompt in English. The downstream AIVJ workflow on the venue machine is expected to read the top-level `prompt` key from channel `1`.

## Live Console control transport

- Endpoint: `/json?channel=8`
- Payload shape:

```json
{
  "live_console_control": {
    "version": "1.0",
    "request_id": "lc-1760000000000",
    "timestamp_ms": 1760000000000,
    "ops": [
      {
        "op": "pane.set_visibility",
        "target": "prompt",
        "args": { "visible": true }
      }
    ],
    "meta": { "source": "vibelive-skill" }
  }
}
```

Supported pane ids in the bundled control script:

- `viewer`
- `viewerAux`
- `settings`
- `prompt`
- `srt`
- `sketch`
- `image`
- `audioRecorder`
- `audioPlayer`
- `midi`
- `gamepad`
