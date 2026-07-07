import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "time": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage()
        }

        if hasattr(record, "extra_data"):
            log_record.update(record.extra_data)

        return json.dumps(log_record)


def setup_logger(app):
    handler = logging.FileHandler("app.json")

    formatter = JSONFormatter()
    handler.setFormatter(formatter)

    handler.setLevel(logging.INFO)

    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)