import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.logger import get_logger
from app.models import DataIn
from app.settings import APP_ID, redis
from app.utils import make_return_txt, write_to_log


logger = get_logger(__name__)


class ConnectionManager:
    def __init__(self):
        """
        All connections are store here as pairs of client_id : [wsConnection, ...]
        """
        self.active_connections: dict = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()

        logger.info(f"wsmanager | Client [{client_id}] connected to {APP_ID}")
    
        if client_id in self.active_connections:
            self.active_connections[client_id].append(websocket)
        else:
            self.active_connections[client_id] = [websocket]

        await self.send_message(client_id)

    async def disconnect(self, client_id: str, websocket: WebSocket):
        self.active_connections[client_id].remove(websocket)
        if not self.active_connections[client_id]:
            del self.active_connections[client_id]
            await redis.delete(client_id)

    async def send_message(self, client_id: str, message: str | None = None):
        if message is None:
            msgdata = json.dumps({"websocket_pid": APP_ID})
        else:
            msgdata = json.dumps({'text': message})

        has_connection = False

        wsconns = self.active_connections.get(client_id, [])
        if wsconns: write_to_log("ws-send", client_id, message)
        else: write_to_log("ws-send", client_id, "<-- unable to send message. no connection found. -->")
        for websocket in wsconns:
            has_connection = True
            await websocket.send_text(msgdata)

        return has_connection


wsmanager = ConnectionManager()
wsrouter = APIRouter()


@wsrouter.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    Websocket conns are long lived
    Once connection is made, this will keep listening for messages
    Once CLIENT_X connects with APP_2, all future **websocket** messages from CLIENT_X will be received by APP_2.
    """
    await wsmanager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            data = json.loads(data)
            input = DataIn(**data)

            write_to_log("ws-recv", client_id, input.text)

            text = make_return_txt(input)
            await wsmanager.send_message(client_id, text)

    except WebSocketDisconnect:
        await wsmanager.disconnect(client_id, websocket)
