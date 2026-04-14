# Blind Access Checker V4.2

This build keeps the working V4.1 audio fix and changes the site analysis model.

## What's new

- uses a **single host voice** instead of a cast of characters
- writes more **nuanced, slightly varied commentary** instead of repetitive play-by-play
- starts with a **blind-user scenario** before exploring the site
- uses a **spider-style route**: home page first, then follows likely internal links
- **returns to the home page** after each route, and also resets when a path behaves strangely
- captures both **focus notes** and **route notes** for the report

## Voice style

The commentary is written to fit a polished accessibility broadcaster with a refined New Zealand-flavoured delivery: calm, articulate, analytical, and lightly witty.

## Quick start

1. Copy `.env.example` to `.env`
2. Add your `OPENAI_API_KEY`
3. Run `setup.bat`
4. Run `run.bat`
5. Open the local URL shown in the terminal

## Notes

- Audio still renders as WAV and combines all narration into `show_mix.wav`.
- The script uses one OpenAI voice by default: `VOICE_HOST`.
- Playwright is still the primary scan engine.
