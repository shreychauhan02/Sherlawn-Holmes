# 🌿 Grass Hunt

Mobile-friendly outdoor scavenger hunt. The Game Master describes the area, Gemma writes
riddles, teams race outside to photograph the answers, and Gemma judges each photo
(correct? outdoors? funny comment?). No database, no login — one Flask file + one HTML page.

## Setup (4 steps)

1. **Install**
   ```bash
   pip install -r requirements.txt
   ```
2. **Set your key** — copy `.env.example` to `.env`, paste your `GEMINI_API_KEY` from
   [AI Studio](https://aistudio.google.com/apikey), and set `GEMMA_MODEL` to the **exact
   Gemma model ID** shown in AI Studio's model list (swap it in `.env` or in `app.py:MODEL` — one line).
3. **Run**
   ```bash
   python app.py
   ```
   The console prints the active model and mode (CLOUD or LOCAL).
4. **Open on your phone** — find your laptop's WiFi IP (`ipconfig` on Windows shows e.g.
   `192.168.1.5`), then on the phone (same WiFi) open `http://192.168.1.5:5000`.
   *Alternative:* deploy to Render as a Web Service pointing at this repo, with
   `GEMINI_API_KEY` set in the service environment, then open the Render URL on any phone.

## Fully offline mode (optional)

```bash
ollama pull gemma3
```
Set `USE_OLLAMA=1` in `.env` and run `python app.py` — photos and riddles are then judged
by the local Gemma model, no internet needed. The header badge on the page shows
`☁️ CLOUD` or `🖧 LOCAL` so you always know which brain is running.

## How a game goes

- Setup: describe the area (5–6 lines), pick language (Hinglish / Hindi / Gujarati / English),
  difficulty (kids / normal / hard), 3–5 rounds, 2–4 team names.
- Each round one team gets a riddle + countdown timer, snaps a photo (compressed to ≤800px
  in the browser before upload), Gemma judges `correct` + `outdoors` with a one-line funny
  comment in your language.
- Scoring: +10 (fast bonus +5), one retry per round worth +5, indoor/screen photos rejected.
- Final screen: winner, Gemma's commentary, downloadable summary, confetti. 🎉

## Files

- `app.py` — everything the server does (Gemma REST calls, defensive JSON parsing with one
  retry, cloud/local switch, error-safe routes).
- `templates/index.html` — the entire game UI (inline CSS + JS, mobile-first, Google Fonts:
  Baloo 2 + Outfit + Noto Sans Devanagari).
- Your API key lives only in `.env`, which `.gitignore` excludes.
