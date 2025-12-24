# F5 AI Guardrail Lab – Frontend Installation Guide
This repository contains a Python Flask–based frontend application that connects to a Python-based AI Guardrail Gateway, which then integrates with F5 Calypso AI Guardrail and a backend LLM (e.g., Ollama).

The frontend does not connect to the LLM directly.
All AI traffic is enforced through the Guardrail layer.

## 1. Architecture Overview
```
Browser (UI)
   ↓
Flask Frontend App (/api/chat)
   ↓
Python Guardrail Gateway (/v1/chat/completions)
   ↓
F5 Calypso AI Guardrail (SaaS)
   ↓
F5 BIG-IP (Enforce System prompt)
   ↓
LLM Runtime (Ollama /api/chat)
```

## 2. System Requirements
- OS: Ubuntu 22.04+ (tested)
- Python: 3.10+
- Network access to:
   - Guardrail Gateway (local)
   - F5 Calypso AI Guardrail (outbound HTTPS)
- LLM runtime (e.g., Ollama) reachable by Calypso AI

## 3. Directory Structure
```
/opt/chatapp
├── main_chat.py
├── templates/
│   └── index.html
└── venv/
```

## 4. Installation Steps
## 4.1 Clone the Repository
```
sudo mkdir -p /opt/chatapp
sudo chown -R $USER:$USER /opt/chatapp
cd /opt/chatapp

git clone https://github.com/JamesLabs1211/ai-guardrail-frontendapp.git
```

## 4.2 Create Python Virtual Environment
```
pip install flask requests urllib3
```

## 5. Environment Variables
The frontend connects to the Guardrail Gateway using environment variables.
## 5.1 Required Variables
```
export GUARDRAIL_GW_BASE_URL="http://127.0.0.1:18080"
export DEFAULT_PROVIDER="<<YOUR PROVIDER NAME in F5 AI Guardrail Portal>>"
```
## 5.2 Optional (if auth is enabled)
The current code doesn't require an auth, but if you need it, please define the token or API key in here.
```
export GUARDRAIL_GW_BEARER="<optional-bearer-token>"
```

## 6. Test the Application Manually
```
source /opt/chatapp/venv/bin/activate
python main_chat.py
```
Access the UI:
```
http://<server-ip>:5000
```

## 7. Run as a Systemd Service (Auto-Start on Reboot)
## 7.1 Create Systemd Service File
```
sudo nano /etc/systemd/system/f5-ai-frontend.service
```
Paste the following:
```
[Unit]
Description=F5 AI Guardrail Frontend (Flask)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/chatapp
Environment=GUARDRAIL_GW_BASE_URL=http://127.0.0.1:18080
Environment=DEFAULT_PROVIDER=james-sg-lab-phi
ExecStart=/opt/chatapp/venv/bin/python /opt/chatapp/main_chat.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```
## 7.2 Enable and Start the Service
```
sudo systemctl daemon-reload
sudo systemctl enable f5-ai-frontend
sudo systemctl start f5-ai-frontend
```
## 7.3 Verify Service Status
```
sudo systemctl status f5-ai-frontend
```
Check logs:
```
journalctl -u f5-ai-frontend -f
```

## 8. Security Notes
- The frontend cannot bypass the Guardrail Gateway
- All AI policy enforcement occurs before LLM inference
- No system prompts or model access is exposed to the UI

## 9. Common Troubleshooting
### UI loads but no response
- Verify Guardrail Gateway is running
- Check GUARDRAIL_GW_BASE_URL
- Inspect logs via journalctl

### JSON parse errors in browser
- Ensure debug=False in Flask
- Ensure backend always returns JSON
