import logging
from datetime import datetime
from pathlib import Path


class Logger:
    def __init__(self, logger_name="TestLogger"):
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False

        if not any(
            isinstance(handler, logging.StreamHandler)
            and not isinstance(handler, logging.FileHandler)
            for handler in self.logger.handlers
        ):
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                )
            )
            self.logger.addHandler(console_handler)

    def configure_file_handler(
        self,
        logs_dir: Path,
        log_file_name: str | None = None,
    ) -> logging.Logger:
        logs_dir.mkdir(parents=True, exist_ok=True)
        log_file = logs_dir / (
            log_file_name or f"framework_{datetime.now().strftime('%Y%m%d')}.log"
        )

        for handler in list(self.logger.handlers):
            if isinstance(handler, logging.FileHandler):
                self.logger.removeHandler(handler)
                handler.close()

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        self.logger.addHandler(file_handler)
        return self.logger

    def get_logger(self) -> logging.Logger:
        return self.logger


_logger_manager = Logger()
logger = _logger_manager.get_logger()
configure_logger = _logger_manager.configure_file_handler
