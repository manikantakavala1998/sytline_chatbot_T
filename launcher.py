"""
Run this file to start the server: python launcher.py
"""

import uvicorn

from backend.app.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "backend.app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )
