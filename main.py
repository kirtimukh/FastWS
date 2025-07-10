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

from models import DataIn
from wsmanager import wsmanager

from logger import get_logger, write_to_log


logger = get_logger(__name__)


REDIS_CHANNEL = "broadcast"
redis = redis.asyncio.from_url("redis://redis:6379", decode_responses=True, db=1)


def make_return_txt(input):
    return f"[pid-{os.getpid()}]  {input.text}"


async def redis_subscriber():
    pubsub = redis.pubsub()
    await pubsub.subscribe(REDIS_CHANNEL)
    logger.info(f"redis     | pid-{os.getpid()} subscribed to channel")

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
    # await init_database()  # this also works
    logger.info(f"lifespan  | Starting up with pid: {os.getpid()}")
    asyncio.create_task(redis_subscriber())
    yield


app = FastAPI(lifespan=lifespan_manager)
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    client_id = ''.join(random.choices(string.ascii_lowercase, k=3))
    return templates.TemplateResponse(
        request=request, name="index.html", context={'session_id': client_id}
    )


@app.post("/submit/{client_id}")
async def http_echo(input: DataIn, client_id: str):
    write_to_log("http_echo", client_id, input.text)

    return {'text': make_return_txt(input)}


@app.post("/without-redis/{client_id}")
async def via_ws(input: DataIn, client_id: str):
    write_to_log("via_ws", client_id, input.text)

    text = make_return_txt(input)
    has_connection = await wsmanager.send_message(client_id, text)

    if has_connection:
        return {'text': f"[pid-{os.getpid()}] replying with ws"}
    else:
        return {'text': f"[pid-{os.getpid()}] no connection to {client_id}"}


@app.post("/with-redis/{client_id}")
async def send_message(input: DataIn, client_id: str):
    write_to_log("Publish", client_id, input.text)

    input_dict = input.model_dump()
    input_dict['pid'] = os.getpid()
    input_dict['client_id'] = client_id

    input_json = json.dumps(input_dict)

    await redis.publish(REDIS_CHANNEL, input_json)
    return {'text': f"[pid-{os.getpid()}] publishing to redis"}


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
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
