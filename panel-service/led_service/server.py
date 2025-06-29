from fastapi import FastAPI
from pydantic import BaseModel
from led_service.protocol import build_packet, make_send_text_payload
from led_service.tcp_client import send_packet

app = FastAPI()

NETWORK_ID = 0x12345678
CARD_ID = 0x01
PANEL_IP = "192.168.1.100"
PANEL_PORT = 5005

class TextRequest(BaseModel):
    window_no: int
    mode: int
    alignment: int
    speed: int
    stay_time: int
    text: str

@app.post("/send-text")
def send_text_command(req: TextRequest):
    payload = make_send_text_payload(req.window_no, req.mode, req.alignment, req.speed, req.stay_time, req.text)
    packet = build_packet(network_id=NETWORK_ID, card_id=CARD_ID, command_code=0x02, payload=payload)
    response = send_packet(PANEL_IP, PANEL_PORT, packet)
    return {"status": "sent", "response": response.hex() if response else None}
