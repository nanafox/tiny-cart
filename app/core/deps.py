from typing import Annotated

from fastapi import Depends, Path, Query
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session
from app.core.settings import settings

from app.db.session import get_session

DBSessionDependency = Annotated[Session, Depends(get_session)]
UserIdDependency = Path(..., description="The user's ID.")
PaginationLimitDependency = Query(
    default=settings.pagination_default_page,
    le=settings.pagination_limit,
    ge=1,
    description="The number of items to return.",
)

OAuth2SchemeDependency = Annotated[
    str, Depends(OAuth2PasswordBearer(tokenUrl=settings.login_route))
]
