import os
import requests
import urllib3
from flask import Flask, request, jsonify, render_template

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# =====================================================
# Guardrail Gateway (FastAPI) configuration
# =====================================================
GUARDRAIL_GW_BASE_URL = os.getenv("GUARDRAIL_GW_BASE_URL", "http://127.0.0.1:18080")
GUARDRAIL_GW_TIMEOUT = int(os.getenv("GUARDRAIL_GW_TIMEOUT", "120"))
GUARDRAIL_GW_BEARER = os.getenv("GUARDRAIL_GW_BEARER", "")  # optional

# Your Calypso provider name (you said you’re using non-OpenAI provider routed to /api/chat)
DEFAULT_PROVIDER = os.getenv("DEFAULT_PROVIDER", "<<YOUR PROVIDER NAME in F5 AI Guardrail Portal")

app = Flask(__name__)

# -------------------------
# Always return JSON errors
# -------------------------
@app.errorhandler(Exception)
def handle_exception(e):
    # Avoid Flask debug HTML pages breaking frontend JSON.parse()
    return jsonify({"error": "Backend exception", "details": str(e)}), 500

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/chat", methods=["POST"])
def api_chat():
    payload_in = request.get_json(silent=True) or {}
    user_message = (payload_in.get("message") or "").strip()

    if not user_message:
        return jsonify({"error": "Message is required"}), 400

    url = GUARDRAIL_GW_BASE_URL.rstrip("/") + "/v1/chat/completions"

    # OpenAI-ish request to your FastAPI gateway
    gw_payload = {
        "provider": DEFAULT_PROVIDER,     # IMPORTANT: set provider explicitly
        "messages": [{"role": "user", "content": user_message}],
        "max_tokens": 256
    }

    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if GUARDRAIL_GW_BEARER:
        headers["Authorization"] = f"Bearer {GUARDRAIL_GW_BEARER}"

    try:
        resp = requests.post(
            url,
            json=gw_payload,
            headers=headers,
            timeout=GUARDRAIL_GW_TIMEOUT,
        )
    except requests.RequestException as e:
        return jsonify({"error": "Failed to reach Guardrail Gateway", "details": str(e)}), 502

    if not resp.ok:
        return jsonify({
            "error": f"Guardrail Gateway HTTP {resp.status_code}",
            "details": resp.text
        }), 502

    # Parse gateway response (OpenAI-ish)
    data = resp.json()
    reply = (
        (data.get("choices") or [{}])[0]
        .get("message", {})
        .get("content")
    )

    if not isinstance(reply, str):
        return jsonify({"error": "Unexpected gateway response format", "raw": data}), 502

    # What your existing frontend JS expects:
    #return jsonify({"reply": reply})
    status = "ok"
    rejection_type = None

    if reply.startswith("Prompt Rejected"):
        status = "rejected"
        rejection_type = "prompt"
    elif reply.startswith("Response Rejected"):
        status = "rejected"
        rejection_type = "response"

    return jsonify({
        "reply": reply,
        "status": status,
        "rejection_type": rejection_type
    })


if __name__ == "__main__":
    # IMPORTANT: keep debug off to avoid HTML tracebacks breaking JSON.parse()
    app.run(host="0.0.0.0", port=5000, debug=False)
