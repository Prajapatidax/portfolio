import pytest
from backend import create_app, db
from backend.services.auth_service import seed_initial_admin
from backend.services.design_service import seed_default_designs


@pytest.fixture
def app():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        seed_initial_admin("Test Admin", "admin@prajapatidax.co.in", "AdminTestPassword123!")
        seed_default_designs()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()
