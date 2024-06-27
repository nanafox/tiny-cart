from datetime import datetime, timedelta

import jwt
from fastapi import HTTPException, status
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from pydantic import UUID4, EmailStr
from sqlmodel import SQLModel

from app import schemas
from app.core import deps
from app.core.deps import DBSessionDependency
from app.core.settings import settings
from app.db import models

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def is_valid_password(*, plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: dict, expires_delta: timedelta | None = None
) -> str:
    """Creates a JWT Access Token for API access."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    to_encode["exp"] = expire
    encoded_jwt = jwt.encode(
        payload=to_encode,
        key=settings.secret_key,
        algorithm=settings.oauth2_algorithm,
    )
    settings.access_token_duration = expire
    return encoded_jwt


async def verify_access_token(
    token: deps.OAuth2SchemeDependency,
    credentials_exception: HTTPException,
) -> schemas.TokenPayload:
    """Verifies that the token being used is valid"""
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.oauth2_algorithm]
        )
        user_id = payload.get("sub")
        email = payload.get("email")
        if user_id is None or email is None:
            raise credentials_exception
        token_data = schemas.TokenPayload(user_id=user_id, email=email)
    except InvalidTokenError as error:
        raise credentials_exception from error

    return token_data


async def get_current_user(
    token: deps.OAuth2SchemeDependency, db: DBSessionDependency
) -> models.User:
    """Returns the current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token_data = await verify_access_token(token, credentials_exception)

    if user := db.get(models.User, token_data.user_id):
        return user
    else:
        raise credentials_exception


class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"
    expires: datetime


class TokenPayload(SQLModel):
    user_id: UUID4
    email: EmailStr
