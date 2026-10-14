# Personal AI podcast: instructions for Claude Code

This folder is a self-running personal podcast: Claude researches the news, writes a short script, ElevenLabs reads it aloud, and the MP3 lands in a private RSS feed served from Dropbox.

## If `show.json` has `"configured": false`: run the setup interview

Welcome the user in one or two sentences, then ask the questions below **one at a time** (use AskUserQuestion when it's available). Offer sensible defaults and keep going even when the answer is short.

1. **What is the show for?** Who listens (just you, or friends or a team you will share it with), and what should they get out of each episode?
2. **Topics.** Three to five areas to follow (e.g. AI and agents, healthcare policy, markets, a specific industry). Anything to always skip?
3. **The listener.** For a personal show: your role, what you already know well, and what you're trying to achieve. For a shared show: who the audience is. Skip anything personal.
4. **Tone.** Any reference programme or style? (e.g. calm public-radio analysis, brisk newsletter, mentor-like.) Opening greeting and sign-off?
5. **Language, length and schedule.** e.g. English, 5 minutes, Mon/Wed/Fri 06:30, plus a timezone.
6. **Name and tagline.** Offer three suggestions built from the answers above, and let the user pick one or write their own.
7. **Voice.** Ask them to choose a voice in the ElevenLabs Voice Library (elevenlabs.io → Voices) that suits the language and tone, and paste its voice ID. Suggest calm narrator or news voices.
8. **Dropbox path.** This folder's path inside Dropbox, e.g. `/Podcasts/My Show`. Check it against the folder's real location on disk (often under `~/Library/CloudStorage/Dropbox/` or `~/Dropbox/`).

Then do the following:

- **Fill in `show.json`.** Set `configured` to true. Choose cover colours that fit the tone.
- **Write `editorial-notes.md`** from `editorial-notes.template.md`, using the answers. Be concrete: the notes drive every episode. For a shared show, fill in the "Content rules for a shared show" section; for a personal show, delete it.
- **Make the cover:** run `python3 cover.py` (it needs Pillow: `pip install pillow`). Show the result and adjust the colours if the user wants.
- **Install the permissions:** create `.claude/settings.json` from `claude-settings.json`.
- **Walk the user through the remaining steps in "Setup" in `README.md`:** `.env`, the Dropbox app, a test episode, the podcast app and the scheduled task. Offer to run the test episode right away by following `RUN.md`.

Never ask the user to paste API keys into the chat. They write them into `.env` themselves.

## If `show.json` has `"configured": true`

- **"Make an episode", "run the show", or a scheduled run:** follow `RUN.md`.
- **Feedback** ("less X", "more Y", "shorter"): add it, dated, to the top of the Feedback section in `editorial-notes.md`, and adjust other sections if the change is structural.
- Never open, print or copy `.env`.
