# Personal AI podcast kit

A self-running personal news podcast. On a schedule, Claude Code researches what happened since the last episode, writes a short script for your topics in your chosen tone, ElevenLabs reads it aloud, and the episode appears in your podcast app through a private RSS feed served from Dropbox.

```
research (Claude Code) → episodes/DATE.txt → tts.py (ElevenLabs) → DATE.mp3 → publish.py (Dropbox links) → feed.xml → podcast app
```

## What you need
- A Mac (or another always-on machine) with [Claude Code](https://code.claude.com) and the Claude desktop app, plus Dropbox syncing to the file system
- An [ElevenLabs](https://elevenlabs.io) API key. Pay-as-you-go works; a 5-minute episode costs roughly $0.30–0.40 at current v4 prices.
- Python 3.9+. `cover.py` also needs Pillow.

## Setup
1. **Put this folder inside your Dropbox**, e.g. `Dropbox/Podcasts/My Show/`.
2. **Open Claude Code in the folder** and say hello. Because `show.json` isn't configured yet, Claude interviews you about the show's purpose, topics, tone, language, schedule, name and voice. It then writes `show.json` and `editorial-notes.md`, makes the cover and installs the permissions.
3. **Secrets:** `cp .env.example .env`, then fill it in yourself. Never paste keys into a chat.
   - `ELEVENLABS_API_KEY`: create a separate key and give it a monthly spending limit.
   - **Dropbox app:** create one at [dropbox.com/developers/apps](https://www.dropbox.com/developers/apps) with *Scoped access*, *Full Dropbox*, and the permissions `files.metadata.read`, `sharing.read` and `sharing.write`. Click **Submit** after ticking them. Put the App key and App secret into `.env`, then run `python3 publish.py --auth` and add the refresh token it prints.
4. **Test episode:** ask Claude Code to "make an episode now". It follows `RUN.md`.
5. **Subscribe:** run `python3 publish.py --feed-link` and add the URL it prints in your podcast app. In Apple Podcasts: Library → ⋯ → *Follow a Show by URL*.
6. **Schedule it:** Claude desktop app → Code → *Scheduled* → new task. Set the folder to this folder, the schedule to your chosen days and time, and the prompt to *"Make today's episode following RUN.md."* Run it once by hand to approve permissions. Keep the machine awake at that time.

## Steering the show
Tell Claude Code "less X, more Y" in this folder, or edit the Feedback section of `editorial-notes.md` yourself. The next episode follows it.

## Privacy
The feed is *unlisted*, not private. It's marked `itunes:block` / `podcast:block` so it stays out of podcast directories, and the Dropbox links are unguessable, but anyone who has the feed URL can listen. You can revoke the links at any time in Dropbox → Shared links. Don't put anything in a personal show that you couldn't live with leaking.

## Files
| File | What it is |
|---|---|
| `CLAUDE.md` | First-run setup interview and standing instructions for Claude Code |
| `RUN.md` | The episode routine |
| `show.json` | Show settings (title, language, voice, Dropbox path, cover colours) |
| `editorial-notes.md` | Created at setup: audience, tone, rules, feedback and episode log |
| `tts.py` / `publish.py` / `cover.py` | Audio, feed and cover. Standard library only, except Pillow for the cover |
| `claude-settings.json` | Permissions, installed to `.claude/settings.json` at setup |
