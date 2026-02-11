import os
import tempfile

import pytest

from app import app, db


@pytest.fixture(scope="session")
def app_instance():
    app.config.update(TESTING=True)
    return app


@pytest.fixture(autouse=True)
def app_context(app_instance):
    ctx = app_instance.app_context()
    ctx.push()
    yield
    ctx.pop()


@pytest.fixture
def client(app_instance):
    return app_instance.test_client()


@pytest.fixture
def db_session(app_instance):
    # Use a file-based sqlite DB to keep data across request contexts.
    db_fd, db_path = tempfile.mkstemp()
    app_instance.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    db.session.remove()
    db.drop_all()
    db.create_all()
    try:
        yield db
    finally:
        db.session.remove()
        db.drop_all()
        os.close(db_fd)
        os.unlink(db_path)
