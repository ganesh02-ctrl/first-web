"""Entry point for running the SSS backend.

Development:  python run.py
Production :  waitress-serve --host=0.0.0.0 --port=5000 run:app
"""
import os

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(
        host=os.getenv("BACKEND_HOST", "127.0.0.1"),
        port=int(os.getenv("BACKEND_PORT", "5000")),
        debug=app.config.get("DEBUG", False),
    )
