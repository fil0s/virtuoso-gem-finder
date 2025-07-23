import logging
import uuid
from pythonjsonlogger import jsonlogger

def get_structured_logger(name="VirtuosoGemHunter"):
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(name)s %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
    return logger

def new_scan_id():
    return str(uuid.uuid4())

def new_token_id():
    return str(uuid.uuid4()) 