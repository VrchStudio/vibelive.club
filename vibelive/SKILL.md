---
name: vibelive
description: Use when an OpenClaw agent must read the live event mood from the VRCH image sender camera feed on vrch-08, summarize the scene vibe, and send a prompt through the VRCH prompt sender websocket interface to steer the on-site AIVJ visuals.
---

# vibelive

This skill is for the `vrch-08` party setup only. It assumes the venue camera feed is being pushed by the deployed VRCH `Image WebSocket Sender` in `Camera` mode, and that the AIVJ workflow is listening to the deployed `Prompt WebSocket Sender` payload on the same host.

## Use this skill when

- You need one fresh live frame from the venue before making a visual decision.
- You need to give a short vibe readout such as crowd energy, lighting feel, color mood, or movement density.
- You need to push a new AIVJ prompt to the LED / big-screen visuals on `vrch-08`.

## Minimal setup

Install the two Python deps once:

```bash
python3 -m pip install -r vibelive/scripts/requirements.txt
```

Default event settings are already bundled in [assets/vrch_08_party.json](assets/vrch_08_party.json).

Read [references/vrch_protocol.md](references/vrch_protocol.md) only if you need exact endpoint or payload details.

## Workflow

### 1. Align the venue console

- Open `https://vrch-08.vrch.ai/console`.
- The correct websocket base for this event is `wss://vrch-08.vrch.ai/vrch-ws/`.
- Expected default channels:
  - Prompt sender: `1`
  - Image sender camera feed: `2`
  - Live Console control: `8`
- If the `viewer / settings / prompt / image` panes are hidden, run:

```bash
python3 vibelive/scripts/vrch_live_console_control.py --preset vibe_agent
```

- If no live scene appears, ask the operator on the venue device to open the `Image Sender` pane, switch to `Camera`, and grant camera permission.

### 2. Pull one live frame

Run:

```bash
python3 vibelive/scripts/vrch_capture_frame.py --out /tmp/vrch_live_scene.jpg
```

The script prints JSON and saves the latest live frame to the requested path.

If the script times out, do not guess the vibe. First verify that the camera page is open and actively streaming on channel `2`.

### 3. Read the vibe

Use the agent's own vision on the saved image. Keep the readout short and operational:

- `Scene:` what is physically happening
- `Vibe:` 2-5 words for the room energy
- `Screen direction:` one visual direction that fits the current moment

Good examples:

- `Scene: compact crowd, people facing the stage, dim room with phone highlights`
- `Vibe: intimate, expectant, low-light`
- `Screen direction: liquid noir pulses with silver accents and slow bloom transitions`

Do not overstate certainty. If the frame is blurred, blocked, or badly exposed, capture again.

### 4. Send the visual prompt to AIVJ

Prompts should be in English, short, and directly usable by the visual system. Prefer 1-3 sentences. Push only the visual direction, not your reasoning.

Run:

```bash
python3 vibelive/scripts/vrch_send_prompt.py --prompt "liquid chrome club energy, dark room, silver and cyan strobes, slow bloom, reflective haze"
```

Default behavior matches the deployed prompt sender:

- channel `1`
- `ai_enhancement=true`
- `style=base`

Override them only when the operator explicitly wants a different style or route.

### 5. Iterate in short loops

Use this loop:

1. Capture a fresh frame.
2. Read the room briefly.
3. Send one prompt.
4. Wait for the screen response.
5. Re-capture before the next change.

For a live party, avoid prompt spam. One deliberate change beats five speculative ones.

## Commands

Capture the latest live frame:

```bash
python3 vibelive/scripts/vrch_capture_frame.py --out /tmp/vrch_live_scene.jpg
```

Send a new visual prompt:

```bash
python3 vibelive/scripts/vrch_send_prompt.py --prompt "dense neon crowd pulse, deep blacks, warm magenta edges, kinetic grain"
```

Show the core Live Console panes:

```bash
python3 vibelive/scripts/vrch_live_console_control.py --preset vibe_agent
```

## Failure rules

- If `/image` yields only text and no binary frame, the sender page is connected but no actual image stream is arriving.
- If a frame arrives but the mood is unreadable, capture again instead of improvising.
- If `/json` prompt sends succeed but visuals do not react, verify the AIVJ workflow is listening on prompt channel `1`.
- If the console looks misrouted, re-check the websocket base against [references/vrch_protocol.md](references/vrch_protocol.md).
