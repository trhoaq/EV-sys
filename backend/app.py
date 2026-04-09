from __future__ import annotations

import sys
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend import create_app
from backend.extensions import socketio

app = create_app()


if __name__ == "__main__":
    socketio.run(
        app,
        host=app.config["FLASK_RUN_HOST"],
        port=app.config["FLASK_RUN_PORT"],
        debug=app.config["DEBUG"],
    )
