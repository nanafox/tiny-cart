from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app import schemas
from app.core.settings import settings
from app.crud.base import APICrudBase
from app.db import models


class UserCrud(APICrudBase[models.User, schemas.User]):
    """
    CRUD operations for the User model.

    This class provides methods to create, retrieve, update, and delete User
    objects.
    It inherits from the APICrudBase class and specifies the User model and
    UserBase schema as type parameters.
    """

    def __init__(self, model: models.User = models.User):
        """
        Initialize the UserCrud class.

        Args:
            model (models.User, optional): The User model. Defaults to
            models.User.
        """
        super().__init__(model)

    def get_by_username(self, *, username: str, db: Session) -> models.User:
        """
        Get a user by username.

        Args:
            username (str): The username of the user.
            db (Session): The database session.

        Returns:
            models.User: The user with the specified username.

        Raises:
            HTTPException: Error 404 if the user is not found.
        """
        if user := db.exec(
            select(models.User).where(models.User.username == username)
        ).first():
            return user

        raise self.not_found_error

    def get_by_email(self, *, email: str, db: Session) -> models.User:
        """
        Get a user by email.

        Args:
            email (str): The email of the user.
            db (Session): The database session.

        Returns:
            models.User: The user with the specified email.

        Raises:
            self.not_found_error: If the user is not found.
        """
        if user := db.exec(
            select(models.User).where(models.User.email == email)
        ).first():
            return user

        raise self.not_found_error

    def create(
        self,
        *,
        db: Session,
        user: schemas.UserCreate,
    ) -> models.User:
        """
        Create a new user.

        Args:
            db (Session): The database session.
            user (schemas.UserCreate): The user data to create.

        Returns:
            models.User: The created user.

        Raises:
            HTTPException: If the user already exists.
        """
        try:
            db_user = super().create(db=db, schema=user)
        except IntegrityError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="user already exists",
            ) from e
        else:
            return db_user

    def get_orders(
        self,
        db: Session,
        user_id: str,
        skip: int = 0,
        limit: int = settings.pagination_limit,
    ) -> list[models.Order]:
        """
        Get the orders of a user.

        Args:
            db (Session): The database session.
            user_id (str): The ID of the user.
            skip (int, optional): The number of orders to skip. Defaults to 0.
            limit (int, optional): The maximum number of orders to retrieve.
            Defaults to settings.pagination_limit.

        Returns:
            list[models.Order]: The orders of the user.
        """
        limit = min(limit, settings.pagination_limit)
        user = self.get_by_id(db=db, obj_id=user_id)
        return user.orders[skip : skip + limit]  # noqa: E203

    def get_products(
        self,
        db: Session,
        user_id: str,
        skip: int = 0,
        limit: int = settings.pagination_default_page,
    ) -> list[models.Product]:
        """
        Get the products of a user.

        Args:
            db (Session): The database session.
            user_id (str): The ID of the user.
            skip (int, optional): The number of products to skip.
            Defaults to 0.
            limit (int, optional): The maximum number of products to retrieve.
            Defaults to settings.pagination_limit.

        Returns:
            list[models.Product]: The products of the user.
        """
        limit = min(limit, settings.pagination_limit)
        user = self.get_by_id(db=db, obj_id=user_id)
        return user.products[skip : skip + limit]  # noqa: E203

    def __get_user(
        self, *, by: str, identifier: str, db: Session
    ) -> models.User:
        """
        Retrieves a user by their ID or username.

        Args:
            by (str): The type of data to use for the search.
            identifier (str): A unique value that identifiers a user.
            db (Session): The database session instance.

        Raises:
            HTTPException: Error 404 is raised if the user does not exist.
            Error 500 is raised if the search type is not recognized.

        Returns:
            models.User: The user with the requested ID or username.
        """
        match by:
            case "id":
                return self.get_by_id(obj_id=identifier, db=db)
            case "username":
                return self.get_by_username(username=identifier, db=db)
            case "email":
                return self.get_by_email(email=identifier, db=db)
            case _:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={
                        "message": "An error while performing this action",
                        "next_steps": "If the error persists, please contact "
                        "the system administrator.",
                    },
                )

    get = __get_user


crud_user = UserCrud()
