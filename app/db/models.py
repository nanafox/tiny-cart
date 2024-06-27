from datetime import datetime, timezone
from uuid import UUID, uuid4

import sqlalchemy as sa
from pydantic import EmailStr
from sqlmodel import Field, Relationship, Session, SQLModel

from app import utils
from app.db import session


class Timestamp(SQLModel):
    created_at: datetime = Field(
        default=datetime.now(timezone.utc),
        sa_column_kwargs={"nullable": False},
    )
    updated_at: datetime = Field(
        default=datetime.now(timezone.utc),
        sa_column_kwargs={
            "onupdate": datetime.now(timezone.utc),
            "nullable": False,
        },
    )


class BaseModel(Timestamp):
    def save(self, *, db: Session, created: bool = False):
        """Saves the current object to the database."""
        self.updated_at = (
            self.created_at if created else datetime.now(timezone.utc)
        )
        return session.save(self, db=db)

    def delete(self, *, db: Session):
        """Deletes the current object from the database."""
        session.delete(self, db=db)


class User(BaseModel, table=True):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    role: str
    username: str = Field(max_length=30, index=True, unique=True)
    user_id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    password: str
    orders: list["Order"] = Relationship(back_populates="order_owner")
    products: list["Product"] = Relationship(back_populates="product_owner")

    def __repr__(self):
        return f"User {self.username}"

    def __str__(self):
        return self.username

    # hash the password before saving it
    def save(self, *, db: Session, created: bool = False):
        self.password = utils.hash_password(password=self.password)
        return super().save(db=db, created=created)


class Product(BaseModel, table=True):
    """
    Represents a product in the inventory.

    Attributes:
        description (str): The description of the product.
        name (str): The name of the product.
        in_stock (bool): Indicates if the product is in stock.
        number_in_stock (int): The number of units of the product in stock.
        unit_price (float): The unit price of the product.
        product_owner_id (UUID): The ID of the user who owns the product.
        product_id (UUID): The unique ID of the product (primary key).

    Relationships:
        orders (list[Order]): The list of orders that include this product.
        product_owner (User): The user who owns the product.
        images (list[Image]): The list of images associated with the product.
    """

    description: str
    name: str
    in_stock: bool
    number_in_stock: int
    unit_price: float = Field(sa_column=sa.Column(sa.Numeric(10, 2)))
    product_owner_id: UUID = Field(
        sa_column=sa.Column(
            sa.ForeignKey("user.user_id", ondelete="CASCADE"),
            nullable=False,
        )
    )
    product_id: UUID = Field(
        default_factory=uuid4, primary_key=True, index=True
    )

    orders: list["Order"] = Relationship(back_populates="products")
    product_owner: "User" = Relationship(back_populates="products")
    images: list["Image"] = Relationship(back_populates="product")

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.name


# Orders model
class Order(BaseModel, table=True):
    """
    Represents an order in the system.

    Attributes:
        order_id (UUID): The unique identifier for the order.
        product_id (UUID): The unique identifier for the product associated
        with the order. This is a foreign key to the product table.
        user_id (UUID): The unique identifier for the user who placed the
        order.
        quantity (int): The number of items in the order.
        products (list[Product]): The list of products associated with the
        order.
        order_owner (User): The user who owns the order.
    """

    order_id: UUID = Field(
        default_factory=uuid4, primary_key=True, index=True
    )
    product_id: UUID = Field(
        sa_column=sa.Column(
            sa.ForeignKey("product.product_id", ondelete="CASCADE"),
            nullable=False,
            default=uuid4,
        )
    )
    user_id: UUID = Field(
        sa_column=sa.Column(
            sa.ForeignKey("user.user_id", ondelete="CASCADE"),
            nullable=False,
        ),
    )
    quantity: int = Field(default=1, description="The number of items")
    products: list["Product"] = Relationship(back_populates="orders")
    order_owner: "User" = Relationship(back_populates="orders")

    def __str__(self) -> str:
        return f"Order {self.order_id}"

    def __repr__(self) -> str:
        return f"Order {self.order_id}"


class Image(BaseModel, table=True):
    """
    Represents an image associated with a product.

    Attributes:
        image_id (UUID): The image's ID.
        file_path (str): The file path of the image.
        product_id (UUID): The ID of the associated product.
        product (Product): The associated product object.
    """
    image_id: UUID = Field(
        default_factory=uuid4,
        description="The image's ID.",
        primary_key=True,
        index=True,
    )
    file_path: str
    product_id: UUID = Field(
        sa_column=sa.Column(
            sa.ForeignKey("product.product_id", ondelete="CASCADE"),
            nullable=False,
        )
    )

    product: "Product" = Relationship(back_populates="images")
