from typing import Generic, TypeVar

from fastapi import HTTPException, status
from sqlmodel import Session, SQLModel, select
from app.core.settings import settings

ModelType = TypeVar("ModelType")
SchemaType = TypeVar("SchemaType", bound=SQLModel)


class APICrudBase(Generic[ModelType, SchemaType]):
    """
    Base class for API CRUD operations.

    Args:
        ModelType: The type of the model.
        SchemaType: The type of the schema.

    Attributes:
        model: The model used for CRUD operations.
        model_name: The name of the model in lowercase.

    Methods:
        get_detailed_error: Returns a detailed error message.
        get_by_id: Returns a single object by its id.
        get_all: Returns all objects of the model.
        create: Creates a new object.
        update: Updates an existing object.
        delete: Deletes an object.
    """

    def __init__(self, model: ModelType):
        self.model = model
        self.model_name = model.__name__.lower()
        self.not_found_error = HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{self.model_name} not found",
        )

    @staticmethod
    def get_detailed_error(error: Exception):
        """
        Returns a detailed error message.

        Args:
            error: The exception object.

        Returns:
            The detailed error message.
        """
        try:
            detail_error = error.args[0].split("\n")[1]
        except IndexError:
            return "The data provided is not correct"

        detail_error = detail_error.replace("DETAIL:  Key ", "")
        detail_error = (
            detail_error.replace("(", "").replace(")=", " ").replace(")", "")
        )
        detail_error = detail_error.replace('"', "'")
        return detail_error

    def get_by_id(self, *, db: Session, obj_id: str) -> ModelType:
        """
        Returns a single object by its id.

        Args:
            db: The database session.
            obj_id: The id of the object.

        Returns:
            The object with the specified id.

        Raises:
            HTTPException: If the object is not found.
        """
        if obj := db.get(self.model, obj_id):
            return obj

        raise self.not_found_error

    def get_all(
        self,
        *,
        db: Session,
        skip=0,
        limit=settings.pagination_default_page,
        order_by=None,
        join_model=None,
    ):
        """
        Returns all objects of the model.

        Args:
            db: The database session.
            skip: The number of objects to skip.
            limit: The maximum number of objects to return.
            order_by: The field to order the objects by.

        Returns:
            A list of all objects.

        Raises:
            HTTPException: If there is an error fetching the objects.
        """
        try:
            query = select(self.model)

            if join_model:
                query = query.join(join_model)

            if order_by:
                query = query.order_by(order_by)

            return db.exec(query.offset(skip).limit(limit)).all()
        except Exception as error:
            raise HTTPException(
                detail={
                    "message": f"Error fetching {self.model_name} objects",
                    "reason": str(error).replace('"', "'"),
                },
                status_code=status.HTTP_400_BAD_REQUEST,
            ) from error

    def create(
        self,
        db: Session,
        schema: SchemaType,
    ):
        """
        Creates a new object.

        Args:
            db: The database session.
            schema: The schema object containing the data for the new object.

        Returns:
            The created object.

        Raises:
            Exception: If there is an error during creation.
        """
        try:
            obj = self.model.model_validate(schema)
            return self.model(**obj.model_dump()).save(db=db, created=True)
        except Exception as error:
            raise error

    def update(
        self,
        *,
        db: Session,
        schema: SchemaType,
        obj_id: str,
        obj_owner_id: str,
    ):
        """
        Updates an existing object.

        Args:
            db: The database session.
            schema: The schema object containing the updated data.
            obj_id: The id of the object to update.
            obj_owner_id: The id of the owner of the object.

        Returns:
            The updated object.

        Raises:
            HTTPException: If the user is not authorized to update the object
            or if there is an error during update.
        """
        db_obj = self.get_by_id(db=db, obj_id=obj_id)
        if obj_owner_id != obj_id:
            raise HTTPException(
                detail="You are not authorized to update this "
                f"{self.model_name}",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        try:
            return db_obj.sqlmodel_update(
                schema.model_dump(exclude_unset=True)
            ).save(db=db)
        except Exception as error:
            raise HTTPException(
                detail={
                    "message": f"Error updating {self.model_name}",
                    "reason": self.get_detailed_error(error),
                },
                status_code=status.HTTP_400_BAD_REQUEST,
            ) from error

    def delete(
        self,
        *,
        db: Session,
        obj_id: str,
        obj_owner_id: str,
    ):
        """
        Deletes an object.

        Args:
            db: The database session.
            obj_id: The id of the object to delete.
            obj_owner_id: The id of the owner of the object.

        Raises:
            HTTPException: If the user is not authorized to delete the object.
        """
        obj = self.get_by_id(db=db, obj_id=obj_id)
        if obj_owner_id != obj_id:
            raise HTTPException(
                detail="You are not authorized to delete this "
                f"{self.model_name}",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        obj.delete(db=db)
