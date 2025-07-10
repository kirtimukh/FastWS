import json, random, string, os

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.requests import Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import redis.asyncio

from app.models import DataIn
from app.wsmanager import wsmanager

from app.logger import get_logger, write_to_log
from app.settings import APP_ID


logger = get_logger(__name__)


REDIS_CHANNEL = "broadcast"
redis = redis.asyncio.from_url("redis://redis:6379", decode_responses=True, db=1)


def make_return_txt(input):
    return f"[{APP_ID}]  {input.text}"


async def redis_subscriber():
    """
    Connects to redis and polls it for new messages
    With this all workers will view all the messages
    A scalable approach would be to 'tree' up the message OR keep a client-server key-value in some form
    """
    pubsub = redis.pubsub()
    await pubsub.subscribe(REDIS_CHANNEL)
    logger.info(f"redis     | {APP_ID} subscribed to channel")

    async for message in pubsub.listen():
        if message["type"] == "message":
            data = message["data"]
            if isinstance(data, bytes):
                data = data.decode()
            # print(f"Received Redis message: {data}")

            input_dict = json.loads(data)

            client_id = input_dict['client_id']
            input = DataIn(**input_dict)

            write_to_log("Redis", client_id, input.text)

            text = make_return_txt(input)
            await wsmanager.send_message(client_id, text)


@asynccontextmanager
async def lifespan_manager(app: FastAPI):
    """
    Runs on startup
    Set up the environment, dbconns, migrations here
    """
    logger.info(f"lifespan  | Starting up with pid: {os.getpid()}")
    asyncio.create_task(redis_subscriber())
    yield
    logger.info("lifespan  | Shutting down. Bye bye.")


app = FastAPI(lifespan=lifespan_manager)
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")


@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    """
    Websocket connection begins **after** index.html in returned
    APP_ID 1 responding to client_id X doesn't guarantee X's websocket conn will be with APP_1
    """
    client_id = ''.join(random.choices(string.ascii_lowercase, k=3))
    return templates.TemplateResponse(
        request=request, name="index.html", context={'session_id': client_id}
    )


@app.post("/submit/{client_id}")
async def http_echo(input: DataIn, client_id: str):
    """
    Echoes back whatever text the user sends with http with http
    """
    write_to_log("http_echo", client_id, input.text)

    return {'text': make_return_txt(input)}


@app.post("/without-redis/{client_id}")
async def via_ws(input: DataIn, client_id: str):
    """
    HTTP connections are ephemereal, stateless
    Any http request from user are not necessarily received by the worker that has the ws-connection
    """
    write_to_log("via_ws", client_id, input.text)

    text = make_return_txt(input)
    has_connection = await wsmanager.send_message(client_id, text)

    if has_connection:
        return {'text': f"[{APP_ID}] replying with ws"}
    else:
        return {'text': f"[{APP_ID}] no connection to {client_id}"}


@app.post("/with-redis/{client_id}")
async def send_message(input: DataIn, client_id: str):
    """
    Publish messages to redis queue and any worker that has the ws-connection can respond
    """
    write_to_log("Publish", client_id, input.text)

    input_dict = input.model_dump()
    input_dict['pid'] = APP_ID
    input_dict['client_id'] = client_id

    input_json = json.dumps(input_dict)

    await redis.publish(REDIS_CHANNEL, input_json)
    return {'text': f"[{APP_ID}] publishing to redis"}


@app.websocket("/ws/{client_id}")
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

            write_to_log("ws_echo", client_id, input.text)

            text = make_return_txt(input)
            await wsmanager.send_message(client_id, text)

    except WebSocketDisconnect:
        wsmanager.disconnect(client_id, websocket)
