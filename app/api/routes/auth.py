from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import select
from app import schemas
from app.db import models
from app.core.deps import DBSessionDependency
from app.core.settings import settings
from app.core import security

router = APIRouter()


@router.post(
    "/login",
    response_model=schemas.Token,
    status_code=status.HTTP_201_CREATED,
)
async def login(
    user_credentials: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: DBSessionDependency,
) -> schemas.Token:
    invalid_credentials_exception = HTTPException(
        detail="Invalid credentials",
        status_code=status.HTTP_417_EXPECTATION_FAILED,
    )

    query = select(models.User).where(
        models.User.email == user_credentials.username
    )
    user = db.exec(query).first()

    if not user:
        raise invalid_credentials_exception

    if not security.is_valid_password(
        plain_password=user_credentials.password,
        hashed_password=user.password,
    ):
        raise invalid_credentials_exception

    access_token = security.create_access_token(
        data={"sub": str(user.user_id), "email": user.email}
    )

    return {
        "data": schemas.TokenBase(
            access_token=access_token,
            token_type="bearer",
            expires=settings.access_token_duration,
        )
    }
