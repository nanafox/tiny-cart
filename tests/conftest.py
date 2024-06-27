import subprocess

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlmodel import Session, SQLModel

from app.core.settings import settings
from app.db import models
from app.db.session import get_session
from app.main import app


@pytest.fixture(scope="package", autouse=True)
def setup_teardown_test_db():
    """Performs setup and teardown for the test database."""
    print("Setting up")
    subprocess.run(["./setup_test_db.sh"])

    yield

    print("Tearing down")
    subprocess.run(["./teardown_test_db.sh"])


@pytest.fixture
def session():
    """Sets up the session for the test database connection."""

    engine = create_engine(settings.database_test_url)

    SQLModel.metadata.drop_all(bind=engine)
    SQLModel.metadata.create_all(bind=engine)

    with Session(engine) as session:
        yield session


@pytest.fixture
async def api_client(session: Session):
    """Yields a client object to be used for API testing."""

    def override_get_session():
        """
        A fixture to override the default database session used in tests.

        Explanation:
        This fixture yields the provided session for testing purposes and
        ensures that the session is properly closed after the test.

        Returns:
            The database session for testing.
        """
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_session] = override_get_session
    yield AsyncClient(
        base_url="http://testserver", transport=ASGITransport(app=app)
    )


@pytest.fixture
def create_jdoe_user(session: Session) -> models.User:
    """
    Fixture to create a user with username 'jdoe' and password 'my_password'
    in the database.

    This fixture creates a user with specific credentials in the database
    using the provided session.

    Args:
        session (Session): The database session to use for creating the user.

    Returns:
        models.User: The created user object in the database.
    """
    pass
