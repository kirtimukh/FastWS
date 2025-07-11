import random, string

from app.settings import APP_ID
from app.logger import get_logger
from app.settings import redis


logger = get_logger()


def write_to_log(method, client_id, text):
    method = method.ljust(10)
    pid = APP_ID.ljust(6)

    logger.info(f"{method}| {pid} | client [{client_id}] : {text}")


def make_return_txt(input):
    return f"[{APP_ID}]  {input.text}"


async def make_client_id():
    client_id = ''.join(random.choices(string.ascii_lowercase, k=3))
    while await redis.get(client_id) is not None:
        client_id = ''.join(random.choices(string.ascii_lowercase, k=3))
    return client_id
