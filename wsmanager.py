import os, json
from fastapi import WebSocket
from logger import get_logger

logger = get_logger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()

        pid = os.getpid()
        logger.info(f"{client_id} connected at PID {pid}")
    
        if client_id in self.active_connections:
            self.active_connections[client_id].append(websocket)
        else:
            self.active_connections[client_id] = [websocket]
        
        await self.send_message(client_id, json.dumps({"text": f"Connected to PID: {pid}"}))

    def disconnect(self, client_id: str, websocket: WebSocket):
        self.active_connections[client_id].remove(websocket)
        if not self.active_connections[client_id]:
            del self.active_connections[client_id]

    async def send_message(self, client_id: str, message: str):
        wsconns = self.active_connections.get(client_id, [])
        for websocket in wsconns:
            await websocket.send_text(message)


wsmanager = ConnectionManager()
