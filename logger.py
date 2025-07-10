import os, logging
from logging.config import dictConfig


class DevConfig:
    LOGGER_NAME: str = "devLogger"
    LOG_FORMAT: str = "%(service)s | %(asctime)s | %(message)s"
    LOG_LEVEL: str = "DEBUG"
    DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"
    LOG_FILE: str = "records.log"
    TXT_ONLY_FORMAT = "%(message)s"


class ToLogHandler(logging.Handler):
    def __init__(self, filename=DevConfig.LOG_FILE):
        super().__init__()
        self.filename = filename

    def emit(self, record):
        log_entry = self.format(record)
        with open(self.filename, "a", encoding="utf-8") as f:
            f.write(log_entry + "\n")


dictConfig(
    {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "()": "uvicorn.logging.DefaultFormatter",
                "fmt": DevConfig.TXT_ONLY_FORMAT,
                "datefmt": DevConfig.DATE_FORMAT,
            }
        },
        "handlers": {
            "default": {
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "formatter": "default",
            },
            "toLogFile": {
                "()": ToLogHandler,
                "formatter": "default",
            }
        },
        "loggers": {
            DevConfig.LOGGER_NAME: {
                "handlers": ["default", "toLogFile"],
                "level": DevConfig.LOG_LEVEL,
                "propagate": False
            },
        },
    }
)


def get_logger(service_name="default"):
    stdlogger = logging.getLogger(DevConfig.LOGGER_NAME)
    NAME_LENGTH = 12
    padded_name = service_name.ljust(NAME_LENGTH)
    logger = logging.LoggerAdapter(stdlogger, {"service": padded_name})
    return logger


logger = get_logger()


def write_to_log(method, client_id, text):
    method = method.ljust(10)
    pid = str(os.getpid())
    pid = pid.ljust( len(pid)+1 )

    logger.info(f"{method}| client [{client_id}] | {pid} : {text}")
