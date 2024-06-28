from datetime import datetime

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    A class to manage settings for the user management system.

    Explanation:
    This class defines settings for the user management system, including
    database connection details, development mode flag, and password length
    requirements. The settings are loaded from environment variables or a .env

    Args:
    - **db_user**: The username for the database connection.
    - **db_name**: The name of the database.
    - **db_host**: The host of the database (default is "localhost").
    - **db_password**: The password for the database connection.
    - **db_port**: The port for the database connection.
    - **dev**: A flag indicating whether the system is in development mode
    (default is False).
    - **minimum_password_length**: The minimum required length for user
    passwords (default is 8).
    - **maximum_password_length**: The maximum allowed length for user
    passwords (default is 15).
    """

    db_user: str | None = None
    db_name: str
    db_database: str | None = None
    db_host: str = "localhost"
    db_password: str | None = None
    db_port: int | None = None
    dev: bool = False
    minimum_password_length: int = 8
    maximum_password_length: int = 15
    database_url: str | None = None
    database_test_url: str | None = None
    prod_url: str | None = "http://localhost:8000"
    database_type: str = "sqlite"
    model_config = ConfigDict(env_file=".env")
    secret_key: str
    oauth2_algorithm: str = "HS256"
    access_token_expire_minutes: int = 3600
    access_token_duration: datetime | None = None
    api_version: str = "v1"
    login_route: str = f"api/{api_version}/login"
    pagination_limit: int = 100
    pagination_default_page: int = 10


settings = Settings()

if settings.db_database:
    settings.db_name = settings.db_database

if settings.database_type == "sqlite":
    if settings.dev:
        settings.database_url = f"sqlite:///{settings.db_name}_dev.db"
        settings.database_test_url = f"sqlite:///{settings.db_name}_test.db"
    else:
        settings.database_url = f"sqlite:///{settings.db_name}.db"
elif settings.dev:
    settings.database_url = settings.database_url or (
        f"{settings.database_type}://{settings.db_user}:{settings.db_password}"
        f"@{settings.db_host}:{settings.db_port}/{settings.db_name}_dev"
    )
    settings.database_test_url = (
        f"{settings.database_type}://{settings.db_user}:{settings.db_password}"
        f"@{settings.db_host}:{settings.db_port}/{settings.db_name}_test"
    )
else:
    settings.database_url = settings.database_url or (
        f"{settings.database_type}://{settings.db_user}:{settings.db_password}"
        f"@{settings.db_host}:{settings.db_port}/{settings.db_name}"
    )
