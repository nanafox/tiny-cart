from uuid import UUID

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app import schemas, utils
from app.core.settings import settings
from app.crud.base import APICrudBase
from app.db import models


class ProductCrud(APICrudBase[models.Product, schemas.ProductBase]):
    """
    CRUD operations for managing products.
    """

    def __init__(self, model: models.Product = models.Product):
        """
        Initialize the ProductCrud class.

        Args:
            model (Type[models.Product], optional): The model class to use for
            CRUD operations. Defaults to models.Product.
        """
        super().__init__(model)

    def create(
        self,
        *,
        db: Session,
        product: schemas.ProductCreate,
        image_paths: list[str],
    ) -> models.Product:
        """
        Create a new product.

        Args:
            db (Session): The database session.
            product (schemas.ProductCreate): The product data to create.
            image_paths (list[str]): The paths of the product images.

        Returns:
            models.Product: The created product.
        """
        db_product = super().create(db=db, schema=product)

        return self.add_product_images_to_database(
            image_paths=image_paths, db_product=db_product, db=db
        )

    def update(
        self,
        *,
        db: Session,
        product_id: UUID,
        product: schemas.ProductUpdate,
        image_paths: list[str],
    ) -> models.Product:
        """
        Update an existing product.

        Args:
            db (Session): The database session.
            product_id (UUID): The ID of the product to update.
            product (schemas.ProductUpdate): The updated product data.
            image_paths (list[str]): The paths of the updated product images.

        Returns:
            models.Product: The updated product.
        """
        # update the user data
        db_product = self.get_by_id(db=db, product_id=product_id)

        # verify the user is the owner of the product
        if product.product_owner_id != db_product.product_owner_id:
            raise HTTPException(
                detail="You are not authorized to update this product",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        db_product.sqlmodel_update(
            product.model_dump(exclude_unset=True)
        ).save(db=db)

        if image_paths:
            return self.add_product_images_to_database(
                image_paths=image_paths, db_product=db_product, db=db
            )
        else:
            return db_product

    @staticmethod
    def add_product_images_to_database(
        *, image_paths: list[str], db_product: models.Product, db: Session
    ) -> models.Product:
        """
        Add product images to the database.

        Args:
            image_paths (list[str]): The paths of the product images.
            db_product (models.Product): The product to associate the images
            with.
            db (Session): The database session.
        """
        for path in image_paths:
            db_image = models.Image(
                file_path=path, product_id=db_product.product_id
            )
            db.add(db_image)
        db.commit()
        db.refresh(db_product)
        return db_product

    def get_by_id(self, *, db: Session, product_id: str) -> models.Product:
        """
        Get a product by its ID.

        Args:
            db (Session): The database session.
            product_id (str): The ID of the product.

        Returns:
            models.Product: The product with the specified ID.
        """
        return super().get_by_id(db=db, obj_id=product_id)

    def get_all(
        self,
        *,
        db: Session,
        skip: int = 0,
        limit: int = settings.pagination_default_page,
    ) -> list[models.Product]:
        """
        Get all products.

        Args:
            db (Session): The database session.

        Returns:
            list[models.Product]: A list of all products.
        """
        return super().get_all(db=db, skip=skip, limit=limit)

    def delete(
        self, *, db: Session, product_id: str, owner_id: str
    ) -> models.Product:
        """
        Delete a product and it's related objects.

        Args:
            db (Session): The database session.
            product_id (str): The ID of the product to delete.
            owner_id (str): The ID of the product owner.

        Returns:
            models.Product: The deleted product.

        Raises:
            HTTPException: If the user is not authorized to delete the product.
        """
        db_product = self.get_by_id(db=db, product_id=product_id)
        if owner_id != db_product.product_owner_id:
            raise HTTPException(
                detail="You are not authorized to delete this product",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        images = db.exec(
            select(models.Image).where(models.Image.product_id == product_id)
        ).all()

        for image in images:
            utils.delete_image(image.file_path)
            image.delete(db=db)

        # delete related orders
        for order in db_product.orders:
            order.delete(db=db)

        db_product.delete(db=db)

    def get_orders(
        self, *, db: Session, product_id: str
    ) -> list[models.Order]:
        """
        Get all orders for a product.

        Args:
            db (Session): The database session.
            product_id (str): The ID of the product.

        Returns:
            list[models.Order]: A list of orders for the product.
        """
        db_product = self.get_by_id(db=db, product_id=product_id)
        return db_product.orders


crud_product = ProductCrud()
