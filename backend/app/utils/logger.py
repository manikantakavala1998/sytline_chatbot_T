"""
Shared logger so ingestion (and later, request handling) actually prints
what it's doing to the terminal — added because startup used to go
straight from "Waiting for application startup" to "Application startup
complete" with zero visibility into the chunking/embedding/Milvus-insert
steps happening in between.
"""

import logging
import sys

_configured = False


def get_logger(name: str) -> logging.Logger:
    global _configured
    if not _configured:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s  %(levelname)-5s  %(name)s  %(message)s",
            datefmt="%H:%M:%S",
            stream=sys.stdout,
        )
        _configured = True
    return logging.getLogger(name)
