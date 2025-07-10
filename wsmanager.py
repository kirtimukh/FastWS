import os, json
from fastapi import WebSocket
from logger import get_logger, write_to_log

logger = get_logger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict = {}
        self.pid = os.getpid()

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()

        logger.info(f"wsmanager | Client [{client_id}] connected to pid-{self.pid}")
    
        if client_id in self.active_connections:
            self.active_connections[client_id].append(websocket)
        else:
            self.active_connections[client_id] = [websocket]

        await self.send_message(client_id)

    def disconnect(self, client_id: str, websocket: WebSocket):
        self.active_connections[client_id].remove(websocket)
        if not self.active_connections[client_id]:
            del self.active_connections[client_id]

    async def send_message(self, client_id: str, message: str | None = None):
        write_to_log("wsmanager", client_id, message)
        if message is None:
            msgdata = json.dumps({"websocket_pid": self.pid})
        else:
            msgdata = json.dumps({'text': message})

        has_connection = False

        wsconns = self.active_connections.get(client_id, [])
        for websocket in wsconns:
            has_connection = True
            await websocket.send_text(msgdata)

        return has_connection


wsmanager = ConnectionManager()
