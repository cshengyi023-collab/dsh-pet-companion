# dsh-pet-companion · a low-key companion panel for DeepSeek Harness

A pure browser-UI plugin for [DeepSeek Harness](https://github.com/deepseek-ai) desktop / web.
It adds an unobtrusive pill in the bottom-left corner (just a pomodoro countdown); click it to expand
the full panel.

## Features (v0.2)

| Tab | What it does | Cost |
|---|---|---|
| 🍅 Focus | SVG ring pomodoro (25/45/60 presets), task name, today's session/focus stats, end chime, desktop-pet bubble | 0 token |
| 🗒 Todo | Local todo list: check off, set as current focus task, clear completed | 0 token |
| 💧 Reminders | Drink-water / stand-up local reminders with adjustable interval | 0 token |
| 📚 Lesson | Topic in → definition, key points, analogy, self-test question; history + copy | ≈1 model call |
| ✏️ Tutor | Paste a homework question → what it tests, step-by-step reasoning, answer, likely pitfalls | ≈1 model call |
| 🎮 Game / 🎤 Voice | Toggles reserved for a later version | — |

- Panel modes: full / pill (default, least obtrusive) / dot; `Alt+P` to hide or show.
- Settings → "小鲸鲸陪伴" (and the plugin page) turn every feature on/off, switch panel mode, reset today's stats.
- Everything is local (`localStorage`); no telemetry. Lesson/tutor reuse the installed desktop pet's chat model.

## Install

```bash
dsh plugin --profile desktop add https://github.com/cshengyi023-collab/dsh-pet-companion
```

or from a local folder:

```bash
dsh plugin --profile desktop add D:\path\to\dsh-pet-companion
```

Restart DSH and the pill appears in the bottom-left corner.

## More in this repo

- `tools/` — desktop pet control panel (with voice audition), read-aloud station, local companion service.
- `patches/` — local enhancement scripts for third-party plugins (persona, voice presets, press animation, API-key reveal).

See `README.md` for the Chinese documentation and `NOTICE-ARTWORK.md` for artwork/third-party notices.

## License

MIT for our own code. Third-party plugins, characters and artwork belong to their respective authors.
