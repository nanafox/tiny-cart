from fastapi import HTTPException, status
from sqlmodel import Session

from app import schemas
from app.core.settings import settings
from app.crud.base import APICrudBase
from app.crud.products import ProductCrud
from app.db import models


class OrderCrud(APICrudBase[models.Order, schemas.Order]):
    """
    CRUD operations for managing orders.

    This class provides methods to create, retrieve, update, and delete orders.
    """

    def __init__(self, model: models.Order = models.Order):
        super().__init__(model)

    @staticmethod
    def update_product_stock(
        *, product: models.Product, quantity: int, db: Session
    ):
        """
        Update the stock of a product.

        Args:
            product (models.Product): The product to update.
            quantity (int): The quantity to subtract from the product stock.
        """
        product.number_in_stock -= quantity
        if product.number_in_stock == 0:
            product.in_stock = False
        product.save(db=db)

    @staticmethod
    def verify_product_stock(*, product: models.Product, quantity: int):
        """
        Verify that a product has enough stock.

        Args:
            product (models.Product): The product to verify.
            quantity (int): The quantity to verify.

        Raises:
            HTTPException: If the product is out of stock or has insufficient
            stock.
        """
        if product.in_stock is False:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(f"Product {product.name} is out of stock"),
            )

        if product.number_in_stock < quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Product {product.name} has only "
                    f"{product.number_in_stock} items left"
                ),
            )

    def create(
        self, *, db: Session, order: schemas.OrderCreate, user_id: str
    ) -> models.Order:
        """
        Create a new order.

        Args:
            db (Session): The database session.
            order (schemas.OrderCreate): The order data.
            user_id (str): The ID of the user placing the order.

        Returns:
            schemas.OrderPublic: The created order.

        Raises:
            HTTPException: If the product is not found, out of stock, or
            insufficient stock.
        """
        for order_product in order.orders:
            new_order = models.Order.model_validate(
                order_product, update={"user_id": user_id}
            )

            db_product = ProductCrud().get_by_id(
                db=db, product_id=order_product.product_id
            )

            self.verify_product_stock(
                product=db_product, quantity=order_product.quantity
            )

            new_order_product = models.Order(
                order_id=new_order.order_id,
                product_id=order_product.product_id,
                quantity=order_product.quantity,
                user_id=user_id,
            )

            new_order_product.save(db=db, created=True)

            # now let's subtract the quantity bought from the product
            self.update_product_stock(
                db=db, product=db_product, quantity=order_product.quantity
            )
        return new_order_product

    def get_by_id(self, *, db: Session, order_id: str) -> models.Order:
        """
        Retrieve an order by its ID.

        Args:
            db (Session): The database session.
            order_id (str): The ID of the order.

        Returns:
            models.Order: The retrieved order.
        """
        return super().get_by_id(db=db, obj_id=order_id)

    def get_all(
        self,
        *,
        db: Session,
        skip: int = 0,
        limit: int = settings.pagination_default_page,
    ) -> list[models.Order]:
        """
        Retrieve all orders.

        Args:
            db (Session): The database session.

        Returns:
            list[models.Order]: A list of all orders.
        """
        return super().get_all(
            db=db, join_model=models.Product, skip=skip, limit=limit
        )

    def delete(self, db: Session, order_id: str, user_id: str):
        """
        Delete an order.

        Args:
            db (Session): The database session.
            order_id (str): The ID of the order to delete.
            user_id (str): The ID of the user deleting the order.

        Raises:
            HTTPException: If the user is not authorized to delete the order.
        """
        db_order = self.get_by_id(db=db, order_id=order_id)
        if db_order.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to delete this order",
            )
        db_order.delete(db=db)
        return None

    def update(
        self,
        *,
        db: Session,
        order_id: str,
        orders: schemas.OrderUpdate,
        user_id: str,
    ) -> models.Order:
        """
        Update an order.

        Args:
            db (Session): The database session.
            order_id (str): The ID of the order to update.
            order (schemas.OrderUpdate): The updated order data.
            user_id (str): The ID of the user updating the order.

        Returns:
            models.Order: The updated order.

        Raises:
            HTTPException: If the user is not authorized to update the order.
        """
        db_order = self.get_by_id(db=db, order_id=order_id)
        if db_order.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to update this order",
            )

        for order in orders.orders:
            db_product = ProductCrud().get_by_id(
                db=db, product_id=order.product_id
            )
            self.verify_product_stock(
                product=db_product, quantity=order.quantity
            )

            db_order.sqlmodel_update(
                order.model_dump(exclude_unset=True)
            ).save(db=db)

            self.update_product_stock(
                db=db, product=db_product, quantity=order.quantity
            )

        return db_order


crud_order = OrderCrud()
