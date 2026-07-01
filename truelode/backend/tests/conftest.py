"""Pytest fixtures: in-memory app + db."""
import pytest

from app import create_app
from app.extensions import db
from config import Config


class TestConfig(Config):
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    TESTING = True


@pytest.fixture()
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()
