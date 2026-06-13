"""TRPG Web Console — Flask backend.

Endpoints:
    GET  /                — web UI
    GET  /api/health      — backend status
    GET  /api/campaigns   — list campaigns under DND_CAMPAIGN_ROOT
    POST /api/chat        — relay a prompt to Claude Code CLI, stream events back (SSE)
    POST /api/session/reset — discard current CLI session and start fresh
"""
import json

from flask import Flask, Response, jsonify, request, send_from_directory
from flask_cors import CORS

from bridge import stream_claude
from config import CAMPAIGNS_DIR, HOST, PORT, PROJECT_ROOT
from sessions import get_session, reset_session

WEB_DIR = PROJECT_ROOT / "console" / "web"

app = Flask(__name__, static_folder=str(WEB_DIR / "static"), static_url_path="/static")
CORS(app)


@app.route("/")
def index():
    return send_from_directory(str(WEB_DIR), "index.html")


@app.route("/api/health")
def health():
    sid, is_new = get_session()
    return jsonify({
        "ok": True,
        "campaigns_dir": str(CAMPAIGNS_DIR),
        "campaigns_dir_exists": CAMPAIGNS_DIR.exists(),
        "session_id": sid,
        "session_is_new": is_new,
    })


@app.route("/api/campaigns")
def list_campaigns():
    if not CAMPAIGNS_DIR.exists():
        return jsonify({"campaigns": []})
    items = []
    campaigns_root = CAMPAIGNS_DIR / "campaigns"
    search_root = campaigns_root if campaigns_root.exists() else CAMPAIGNS_DIR
    for entry in sorted(search_root.iterdir()):
        if not entry.is_dir() or entry.name.startswith("_") or entry.name.startswith("."):
            continue
        state_md = entry / "state.md"
        items.append({
            "name": entry.name,
            "path": str(entry),
            "has_state": state_md.exists(),
        })
    return jsonify({"campaigns": items})


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    prompt = (data.get("prompt") or "").strip()
    if not prompt:
        return jsonify({"error": "empty prompt"}), 400

    session_id, is_new = get_session()

    def gen():
        try:
            for event in stream_claude(prompt, session_id=session_id, is_new=is_new):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except Exception as e:
            err = {"type": "error", "text": f"backend exception: {e!r}"}
            yield f"data: {json.dumps(err, ensure_ascii=False)}\n\n"

    headers = {
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
    }
    return Response(gen(), mimetype="text/event-stream", headers=headers)


@app.route("/api/session/reset", methods=["POST"])
def session_reset():
    sid, _ = reset_session()
    return jsonify({"session_id": sid})


if __name__ == "__main__":
    sid, is_new = get_session()
    print(f"[console] project root: {PROJECT_ROOT}")
    print(f"[console] campaigns dir: {CAMPAIGNS_DIR}")
    print(f"[console] session id: {sid} (new={is_new})")
    print(f"[console] serving on http://{HOST}:{PORT}")
    app.run(host=HOST, port=PORT, debug=False, use_reloader=False, threaded=True)
