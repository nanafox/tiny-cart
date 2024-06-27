from typing import Annotated

from fastapi import Depends

from app.core.security import get_current_user
from app.db import models

CurrentUserDependency = Annotated[models.User, Depends(get_current_user)]
UserDependency: models.User = Depends(get_current_user)
