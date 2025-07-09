import json, random, string, os

from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.requests import Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from models import DataIn
from wsmanager import wsmanager

from logger import get_logger
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan_manager(app: FastAPI):
    # await init_database()  # this also works
    logger.info(f"Starting up with pid: {os.getpid()}")
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
    session_id = ''.join(random.choices(string.ascii_lowercase, k=2))
    return templates.TemplateResponse(
        request=request, name="index.html", context={'session_id': session_id}
    )


def write_to_log(session_id, protocol, input):
    return logger.info(f"Pid: {os.getpid()}; {protocol}; {session_id}: {input.text}")


def make_return_txt(input):
    return f"{os.getpid()};  text: {input.text}"


@app.post("/submit/{session_id}")
async def echo(input: DataIn, session_id: str):
    write_to_log(session_id, "HTTP", input)

    return {'text': make_return_txt(input)}


@app.post("/http-to-ws/{session_id}")
async def h2w(input: DataIn, session_id: str):
    write_to_log(session_id, " H2W", input)

    text = make_return_txt(input)
    await wsmanager.send_message(session_id, json.dumps({'text': text}))

    return {'text': f"{os.getpid()} responds with ws"}


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await wsmanager.connect(websocket, session_id)
    try:
        while True:
            data = await websocket.receive_text()
            data = json.loads(data)
            input = DataIn(**data)

            write_to_log(session_id, "  WS", input)

            text = make_return_txt(input)
            await wsmanager.send_message(session_id, json.dumps({'text': text}))

    except WebSocketDisconnect:
        wsmanager.disconnect(session_id, websocket)
