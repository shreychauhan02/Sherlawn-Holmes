*This is a submission for the [Hacktoberfest Open-Source AI Challenge Week 1: Touch Grass](https://dev.to/challenges/hacktoberfest-week1-2026-10-05)*

## What I Built
**Grass Hunt** 🌿 — an outdoor scavenger-hunt web app that literally forces players to touch grass.

The Game Master describes their real neighbourhood on a phone (a neem tree, a Hanuman temple, a chai stall…), and an open-weight Gemma 4 model instantly writes riddles in that area's own language — Hinglish, Hindi, Gujarati or English. Teams then race outside against a countdown timer to *find the real thing and photograph it*. A second Gemma call judges every photo: is it the right target, and is it genuinely outdoors (no sneaky photos of a TV screen or Google Images)? Points, retries, funny in-language commentary, a scoreboard, and a Gemma-written sports-commentator recap at the end.

It's for kids, families, housing societies, school camps — anyone whose idea of fun has been stuck behind a screen. The screen is only the starting line and the referee; the game itself happens under the sky.

## Demo
**🔗 LIVE: [https://sherlawn-holmes.onrender.com](https://sherlawn-holmes.onrender.com)** — open it on any phone, no setup needed. (Free Render instance sleeps after ~15 min idle, so the first hit may take 30–60 s to wake up.)

Prefer it offline? Run locally in 4 steps (see README) and open `http://<your-laptop-IP>:5000` on any phone on the same WiFi — or flip `USE_OLLAMA=1` and the whole game runs on a local Gemma model with zero internet.
- Video demo: *(link here)*

## Code
GitHub repo: https://github.com/shreychauhan02/Sherlawn-Holmes

Deliberately tiny — no database, no login, no framework soup:
- `app.py` — one Flask file: Gemma 4 REST calls (cloud *or* local Ollama), defensive JSON parsing, error-safe routes
- `templates/index.html` — the whole mobile-first game UI in one file (inline CSS + JS)

## How I Built It
The brain of the game is **Gemma 4 (`gemma-4-26b-a4b-it`)**, Google's open-weight model, used three ways:
1. **Riddle writer** — one call turns the Game Master's area description into N rhyming scavenger riddles in the chosen language and difficulty.
2. **Photo judge** — a vision call checks `{correct, outdoors, comment}` against each uploaded photo (client-side compressed to ≤800px).
3. **Commentator** — a final call writes the funny match recap.

Gemini's `generateContent` REST endpoint is hit with a single swappable `MODEL` constant, and because Gemma doesn't offer JSON mode, all instructions live in the user prompt and the parser digs the JSON out of the model's reasoning preamble with a retry. A `USE_OLLAMA=1` flag switches the whole game to a **fully offline local Gemma** via Ollama — same code, same game, zero internet.

## Why Does Open Innovation Matter?
A closed, fixed-pricing API would have killed this project twice over. Grass Hunt makes *many* small vision calls per game — one per photo per team — and open weights mean I can run a whole society's tournament on a laptop with `ollama` and no billing anxiety at all. It also means the game runs in a village ground with no internet, schools can self-host it, and anyone can swap in tomorrow's better open model by editing one line. The model is a replaceable part, not a paywall — that's what an open-weight ecosystem makes possible and a closed API doesn't.

## My Agent Session
Built with Qoder (agentic IDE): Flask backend, single-file game UI, live API debugging sessions (model 500s, Gemma 4 reasoning-preamble JSON parsing) all verified end-to-end against the real model.

## Prize Categories
- Open-weight AI / Gemma category
- "Touch Grass" real-world impact

<!-- Team Submissions: solo submission by @shreychauhan02 -->
