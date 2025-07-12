import json, os

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.logger import get_logger
from app.models import DataIn
from app.routes import router
from app.settings import APP_ID, REDIS_CHANNEL, redis
from app.utils import make_return_txt, write_to_log
from app.wsmanager import wsmanager, wsrouter


logger = get_logger(__name__)


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

            write_to_log("redis-app", client_id, input.text)

            text = make_return_txt(input)
            await wsmanager.send_message(client_id, text)


@asynccontextmanager
async def lifespan_manager(app: FastAPI):
    """
    Runs on startup
    Set up the environment, dbconns, migrations here
    """
    logger.info(f"lifespan  | {APP_ID} starting up with pid: {os.getpid()}")
    asyncio.create_task(redis_subscriber())
    yield
    logger.info(f"lifespan  | {APP_ID} shutting down. Bye bye.")


app = FastAPI(lifespan=lifespan_manager)
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(router, prefix="")
app.include_router(wsrouter, prefix="")
