"""Shared Flask extension singletons."""
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
socketio = SocketIO(cors_allowed_origins="*", async_mode="threading")
