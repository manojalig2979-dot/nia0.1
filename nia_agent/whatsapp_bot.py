from fastapi import FastAPI, Request, Form
from fastapi.responses import PlainTextResponse
import uvicorn
from config_manager import load_config
from agent_orchestrator import NiaAgentOrchestrator

app    = FastAPI(title="Nia WhatsApp Gateway")
config = load_config()
agent  = NiaAgentOrchestrator(config)

@app.get("/")
def home():
    return {"status": "Nia Agent WhatsApp Server Online ✅"}

@app.post("/webhook/whatsapp", response_class=PlainTextResponse)
async def whatsapp_webhook(
    From: str = Form(default=""),
    Body: str = Form(default="")
):
    """
    Receives Twilio WhatsApp webhook (form-encoded).
    Twilio sends:  From=whatsapp:+91..., Body=<message text>
    Returns:       TwiML XML so Twilio sends the reply back to the user.
    """
    print(f"[Incoming WhatsApp from {From}]: {Body}")

    if not Body.strip():
        return _twiml("Main samajh nahi paayi. Kuch likhkar bhejiye!")

    # Process through Nia's Agent Brain
    reply = agent.process_command(Body.strip())

    print(f"[Nia Reply]: {reply}")
    return _twiml(reply)


def _twiml(message: str) -> str:
    """Wraps a text reply in Twilio TwiML format."""
    # Escape XML special chars
    safe = message.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<Response>"
        f"<Message>{safe}</Message>"
        "</Response>"
    )


def start_webhook_server(port: int = 8000):
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")


if __name__ == "__main__":
    start_webhook_server()
