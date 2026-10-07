import base64
import json
import os
import re
import time

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

load_dotenv()

app = Flask(__name__)

# ---------------------------------------------------------------------------
# MODEL CONFIG — swap the model in ONE place.
# Copy the EXACT Gemma model ID from https://aistudio.google.com (Model list,
# e.g. "gemma-3-27b-it" or whatever Gemma 4 ID AI Studio shows you) and either
# set GEMMA_MODEL in your .env or edit the default below.
MODEL = os.getenv("GEMMA_MODEL", "gemma-4-26b-a4b-it")

USE_OLLAMA = os.getenv("USE_OLLAMA", "0") == "1"
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3")  # `ollama pull gemma3`

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def call_model(prompt, image_b64=None, mime_type="image/jpeg"):
    """Return the model's raw text reply. Same signature for cloud and local."""
    if USE_OLLAMA:
        payload = {
            "model": OLLAMA_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {"temperature": 0.8},
        }
        if image_b64:
            payload["messages"][0]["images"] = [image_b64]
        r = requests.post(OLLAMA_URL, json=payload, timeout=120)
        r.raise_for_status()
        return r.json().get("message", {}).get("content", "")

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set. Put it in your .env file.")
    parts = [{"text": prompt}]
    if image_b64:
        parts.append({"inlineData": {"mimeType": mime_type, "data": image_b64}})
    payload = {"contents": [{"parts": parts}],
               "generationConfig": {"temperature": 0.8}}
    r = requests.post(
        GEMINI_URL.format(model=MODEL),
        json=payload,
        headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
        timeout=120,
    )
    r.raise_for_status()
    data = r.json()
    try:
        return "".join(p.get("text", "") for p in data["candidates"][0]["content"]["parts"])
    except (KeyError, IndexError):
        raise RuntimeError("Model returned an empty or malformed reply.")


def parse_json_defensive(text):
    """Gemma 4 may prepend a reasoning preamble and wrap JSON in fences.
    Scan for every balanced JSON value and keep the LAST valid one (the answer)."""
    cleaned = re.sub(r"```(json)?", "", text)
    dec = json.JSONDecoder()
    best, best_end = None, -1
    for i, ch in enumerate(cleaned):
        if ch not in "[{":
            continue
        try:
            obj, end = dec.raw_decode(cleaned[i:])
        except ValueError:
            continue
        if isinstance(obj, (list, dict)) and obj and i + end > best_end:
            best, best_end = obj, i + end
    if best is None:
        raise ValueError("Could not parse JSON from model output.")
    return best


def ask_json(prompt):
    """Call the model and parse JSON; retry once on failure with stricter wording."""
    last_err = None
    for attempt in range(2):
        try:
            p = prompt if attempt == 0 else prompt + "\n\nIMPORTANT: Respond with ONLY valid JSON. No markdown, no explanation."
            raw = call_model(p)
            return parse_json_defensive(raw)
        except (ValueError, requests.RequestException, RuntimeError, KeyError) as e:
            last_err = e
            time.sleep(2)
    raise last_err


# ----------------------------- prompts -------------------------------------

def build_riddle_prompt(desc, language, difficulty, rounds):
    return f"""You are the Game Master assistant for "Grass Hunt", an outdoor scavenger hunt for kids and families in India.

Game Master's description of the area:
{desc}

Create EXACTLY {rounds} scavenger-hunt riddle tasks as a strict JSON array. Each item:
{{"id": 1, "riddle": "...", "answer_hint_for_judge": "...", "easy_hint": "..."}}

Rules:
- riddle: 1-2 short fun lines, rhyme or playfulness welcome. Teams must find the thing and photograph it outdoors.
- Things must come from the Game Master's description or common outdoor things (trees, birds, sky, water, stones, flowers, shadows, clouds).
- answer_hint_for_judge: one line telling the photo-judge exactly what photo counts as correct.
- easy_hint: one very obvious hint if the team is stuck.
- Difficulty: {difficulty} ({'very simple, name-adjacent hints' if difficulty == 'kids' else 'moderate wordplay' if difficulty == 'normal' else 'clever indirect riddles'}).
- Write riddle and easy_hint in this language: {language}.
Output ONLY the JSON array, nothing else."""


def build_judge_prompt(riddle, answer_hint, language):
    return f"""You are the friendly judge of an outdoor scavenger hunt called Grass Hunt.

The team had to photograph this: {riddle}
What counts as correct: {answer_hint}

Look at the attached photo and reply with ONLY this JSON object:
{{"correct": true/false, "outdoors": true/false, "comment": "one short funny line in {language}"}}

- "correct": does the photo plausibly show the requested thing? Be generous with kids, use your best guess if blurry.
- "outdoors": is the photo clearly taken OUTDOORS? Not indoors, not a screenshot, not a photo of a TV/phone/computer screen, not a picture from a book or the internet. If you cannot tell, set outdoors to false.
- "comment": a playful one-line remark for the team, in {language}.
Output ONLY the JSON object."""


def build_commentary_prompt(desc, scores, language):
    ranking = ", ".join(f"{t['name']}: {t['score']} pts" for t in sorted(scores, key=lambda x: -x["score"]))
    winner = max(scores, key=lambda x: x["score"])["name"]
    return f"""Grass Hunt scavenger hunt just ended. Area: {desc}
Final scores: {ranking}. Winner: {winner}.

Write ONLY a JSON object: {{"commentary": "3-4 short funny lines of sports-commentator style recap about this hunt, in {language}. Mention the winner cheeringly. Keep it under 60 words."}}
Output ONLY the JSON object."""


# ------------------------------- routes -------------------------------------

@app.route("/")
def index():
    return render_template("index.html", model=MODEL, mode="local" if USE_OLLAMA else "cloud")


@app.route("/api/riddles", methods=["POST"])
def riddles():
    d = request.get_json(force=True, silent=True) or {}
    desc = (d.get("desc") or "").strip()
    if len(desc) < 10:
        return jsonify(error="Please write at least a line or two about the area."), 400
    prompt = build_riddle_prompt(desc, d.get("language", "English"),
                                 d.get("difficulty", "normal"),
                                 max(3, min(5, int(d.get("rounds", 3)))))
    try:
        data = ask_json(prompt)
        if not isinstance(data, list) or not data:
            raise ValueError("Model did not return a riddle list.")
        out = [{"id": i + 1,
                "riddle": str(x.get("riddle", "")),
                "answer_hint_for_judge": str(x.get("answer_hint_for_judge", "")),
                "easy_hint": str(x.get("easy_hint", "Look around you!"))}
               for i, x in enumerate(data)]
        return jsonify(riddles=out)
    except Exception as e:
        return jsonify(error=f"Could not generate riddles ({type(e).__name__}). Check the key/model and try again."), 502


@app.route("/api/judge", methods=["POST"])
def judge():
    d = request.get_json(force=True, silent=True) or {}
    img = d.get("image") or ""
    img = img.split(",", 1)[-1] if img.startswith("data:") else img
    if not img:
        return jsonify(error="No photo received. Please take a photo first!"), 400
    try:
        prompt = build_judge_prompt(d.get("riddle", ""),
                                    d.get("answer_hint", "the described outdoor thing"),
                                    d.get("language", "English"))
        data = None
        last_err = None
        for attempt in range(2):
            try:
                p = prompt if attempt == 0 else prompt + "\n\nRespond with ONLY valid JSON."
                data = parse_json_defensive(call_model(p, image_b64=img))
                break
            except (ValueError, KeyError) as e:
                last_err = e
                time.sleep(2)
        if data is None:
            raise last_err
        return jsonify(correct=bool(data.get("correct")),
                       outdoors=bool(data.get("outdoors")),
                       comment=str(data.get("comment", "Hmm!")))
    except Exception as e:
        return jsonify(error=f"Judge had a brain freeze ({type(e).__name__}). Retake the photo and try once more."), 502


@app.route("/api/commentary", methods=["POST"])
def commentary():
    d = request.get_json(force=True, silent=True) or {}
    scores = d.get("scores") or []
    if not scores:
        return jsonify(commentary="Game over! Go outside again tomorrow.")
    try:
        data = ask_json(build_commentary_prompt(d.get("desc", ""), scores, d.get("language", "English")))
        return jsonify(commentary=str(data.get("commentary", "What a hunt!")))
    except Exception:
        return jsonify(commentary="And the crowd goes wild — Grass Hunt champions, that's you!")


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "5000"))
    mode = "LOCAL (Ollama)" if USE_OLLAMA else "CLOUD (Google AI Studio)"
    print("=" * 46)
    print(f"  Grass Hunt is up  ->  http://localhost:{port}")
    print(f"  Mode : {mode}")
    print(f"  Model: {OLLAMA_MODEL if USE_OLLAMA else MODEL}")
    print("=" * 46)
    app.run(host=host, port=port, debug=False)
