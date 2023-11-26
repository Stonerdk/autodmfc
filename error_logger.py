import logging
from datetime import datetime
from colorlog import ColoredFormatter

#logging.basicConfig(
 #   encoding="utf-8",
  #  level=logging.DEBUG)

# 로그 설정
def logger_init():
    stamp = datetime.now()
    log_file_path = f"./logs/{datetime.strftime(stamp, "%Y%m%d_%H%M%S")}.txt"


    file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logging.getLogger().addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    formatter = ColoredFormatter(
        "%(asctime)s - %(log_color)s%(levelname)-8s%(reset)s - %(message)s",
        datefmt=None,
        reset=True,
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    )

    console_handler.setFormatter(formatter)
    logging.getLogger().addHandler(console_handler)

def _log(port, level, *args):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    message = ' '.join(map(str, args))
    if port:
        message = f'[PORT {port}] {message}'
    logger.log(level, message)

def error(port, *message):
    _log(port, logging.ERROR, *message)

def warning(port, *message):
    _log(port, logging.WARNING, *message)

def succeed(port, *message):
    _log(port, logging.INFO, *message)

def verbose(port, *message):
    _log(port, logging.DEBUG, *message)
