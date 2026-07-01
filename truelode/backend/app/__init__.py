"""Truelode backend application factory."""
from flask import Flask
from flask_cors import CORS

from config import Config

from .api import register_blueprints
from .extensions import db, jwt, migrate, socketio


def create_app(config: type[Config] = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config)

    CORS(app, resources={r"/api/*": {"origins": "*"}})
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    socketio.init_app(app)

    from . import models  # noqa: F401  (register mappers)

    register_blueprints(app)

    @app.get("/api/health")
    def health():
        return {"status": "ok", "service": "truelode"}

    return app
