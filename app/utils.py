from app.settings import APP_ID
from app.logger import get_logger


logger = get_logger()


def write_to_log(method, client_id, text):
    method = method.ljust(10)
    pid = APP_ID.ljust(6)

    logger.info(f"{method}| {pid} | client [{client_id}] : {text}")


def make_return_txt(input):
    return f"[{APP_ID}]  {input.text}"
