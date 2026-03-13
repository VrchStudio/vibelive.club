---
name: vibelive
description: Use when an OpenClaw agent must read the live event mood from the VRCH image sender camera feed on vrch-08, summarize the scene vibe, and send a prompt through the VRCH prompt sender websocket interface to steer the on-site AIVJ visuals.
---

# vibelive

This public entrypoint mirrors the bundled skill in [vibelive/SKILL.md](vibelive/SKILL.md). Download the whole `vibelive/` directory with it so the scripts and event defaults stay available.

## Install once

```bash
python3 -m pip install -r vibelive/scripts/requirements.txt
```

## Event target

- Console: `https://vrch-08.vrch.ai/console`
- Viewer hub: `https://vrch-08.vrch.ai/viewer`
- WebSocket base: `wss://vrch-08.vrch.ai/vrch-ws/`
- Prompt channel: `1`
- Image sender camera channel: `2`
- Live Console control channel: `8`

The bundled default config is [vibelive/assets/vrch_08_party.json](vibelive/assets/vrch_08_party.json).

Protocol details live in [vibelive/references/vrch_protocol.md](vibelive/references/vrch_protocol.md).

## Short workflow

1. Open `https://vrch-08.vrch.ai/console`.
2. Make sure the venue device has `Image Sender -> Camera` open and camera permission granted.
3. If the core panes are hidden, run:

```bash
python3 vibelive/scripts/vrch_live_console_control.py --preset vibe_agent
```

4. Pull one fresh live frame:

```bash
python3 vibelive/scripts/vrch_capture_frame.py --out /tmp/vrch_live_scene.jpg
```

5. Use the agent's own vision on that file and respond briefly with:
   - `Scene`
   - `Vibe`
   - `Screen direction`

6. Push the next AIVJ prompt in English:

```bash
python3 vibelive/scripts/vrch_send_prompt.py --prompt "liquid chrome club energy, dark room, silver and cyan strobes, slow bloom, reflective haze"
```

## Operating rules

- Capture before every prompt change.
- Keep vibe feedback short and concrete.
- Do not fake certainty from a bad frame; re-capture instead.
- Keep prompts visual-only and concise.
- If prompt sends do nothing, verify the AIVJ workflow is listening on `/json` channel `1`.
