from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Generic, TypeVar
from uuid import UUID

from fastapi import status
from pydantic import UUID4, EmailStr, HttpUrl, model_validator
from sqlmodel import Field, SQLModel

import app
import app.main
from app.db import models

ResponseModel = TypeVar("ResponseModel")


class BaseResponse(SQLModel, Generic[ResponseModel]):
    message: str
    status_code: int
    success: bool = True
    url: HttpUrl | None = Field(default=None, exclude=True)
    count: int | None = Field(
        default=None, description="The number of items.", exclude=True
    )
    data: ResponseModel

    @model_validator(mode="before")
    @classmethod
    def compute_count(cls, values):
        """
        Computes the number of items in the data list.

        Args:
            values (dict): The values passed to the model.

        Returns:
            dict: The updated values with the correct count.
        """
        if "data" in values and isinstance(values["data"], list):
            values["count"] = len(values["data"])

        return values


class UserRoles(str, Enum):
    seller = "seller"
    buyer = "buyer"


class ProductBase(SQLModel):
    """
    Represents the base schema for a product.
    """

    description: str = Field(description="The product's description.")
    name: str = Field(description="The product's name.")
    in_stock: bool = Field(description="The product's stock status.")
    number_in_stock: int = Field(default=0)
    unit_price: float = Field(description="The product's price.")


class ProductCreate(ProductBase):
    """
    Represents the schema for creating a product.
    """

    product_owner_id: UUID4


class ProductUpdate(SQLModel):
    """
    Represents the schema for updating a product.
    """

    description: str | None = Field(
        default=None, description="The product's description."
    )
    name: str | None = Field(default=None, description="The product's name.")
    in_stock: bool | None = Field(
        default=None, description="The product's stock status."
    )
    unit_price: float | None = None
    number_in_stock: int | None = None
    product_owner_id: UUID4


class Product(ProductBase, models.Timestamp):
    """
    Represents the public schema for a product.
    """

    product_id: UUID4
    orders: list[OrderInUserResponse]
    product_owner: UserInProductResponse
    images: list[ImageResponse]


class ProductPublic(BaseResponse[Product]):
    """
    Represents the public schema for a product.
    """

    message: str = "Product retrieved successfully."
    status_code: int = status.HTTP_200_OK
    data: Product


class ProductsPublic(BaseResponse[Product]):
    """
    Represents a list of public products.
    """

    message: str = "Products retrieved successfully."
    status_code: int = status.HTTP_200_OK
    data: list[Product]


class ProductInModels(SQLModel):
    """
    Represents the schema for a product used in other models.
    """

    product_id: UUID4
    name: str
    unit_price: float


# User schemas
class UserBase(SQLModel):
    """
    Represents the base schema for a user.
    """

    email: EmailStr = Field(unique=True, index=True, max_length=255)
    role: UserRoles = Field()
    username: str = Field(max_length=30, index=True, unique=True)


class UserWithTimestamp(models.Timestamp, UserBase):
    """
    Represents the schema for a user with timestamp.
    """

    pass


# Properties to receive via API on creation
class UserCreate(UserBase):
    """
    Represents the schema for creating a user.
    """

    password: str = Field(min_length=8, max_length=40)


# Properties to receive via API on update, all are optional
class UserUpdate(SQLModel):
    """
    Represents the schema for updating a user.
    """

    email: EmailStr | None = Field(default=None, max_length=255)
    username: str | None = Field(
        default=None, max_length=30, index=True, unique=True
    )
    role: UserRoles | None = Field(default=None)


class UserPasswordUpdate(SQLModel):
    """
    Represents the schema for updating a user's password.
    """

    current_password: str = Field(default=None, min_length=8, max_length=40)
    new_password: str = Field(default=None, min_length=8, max_length=40)


class ProductInUserResponse(SQLModel):
    product_id: UUID4
    name: str
    description: str
    unit_price: float
    number_in_stock: int
    in_stock: bool


class ProductsInUserResponse(BaseResponse[ProductInUserResponse]):
    message: str = "User products retrieved successfully."
    status_code: int = status.HTTP_200_OK
    count: int
    data: list[ProductInUserResponse]


class User(UserWithTimestamp):
    user_id: UUID4

    @model_validator(mode="after")
    def remove_products_for_buyer(self):
        """
        Removes the products attribute for buyers.

        Returns:
            UserPublic: The modified UserPublic instance.
        """
        if self.role == "buyer":
            self.__dict__.pop("products", None)

        return self


class UserPublic(BaseResponse[User]):
    message: str = "User retrieved successfully."
    status_code: int = status.HTTP_200_OK
    data: User


class UsersPublic(BaseResponse[User]):
    """
    Represents a list of public users.
    """

    message: str = "Users retrieved successfully."
    status_code: int = status.HTTP_200_OK
    count: int = Field(
        alias="count",
        description="The number of users retrieved.",
    )
    data: list[User]


class UserInModels(SQLModel):
    user_id: UUID4
    username: str


class UserInProductResponse(UserInModels):
    """
    Represents the schema for a user in a product response.
    """

    pass


class UserInOrderResponse(UserInModels):
    """
    Represents the schema for a user in an order response.
    """

    pass


# Schemas for Order
class OrderProductCreate(SQLModel):
    """
    Represents the schema for creating an order product.
    """

    quantity: int = Field(description="The number of items to order")
    product_id: UUID4 = Field(description="The ID of the product")


class OrderCreate(SQLModel):
    """
    Represents the schema for creating an order.
    """

    orders: list[OrderProductCreate]


class OrderUpdate(OrderCreate):
    """
    Represents the schema for updating an order.
    """

    pass


class ProductInOrder(SQLModel):
    product_id: UUID4


class OrderBase(SQLModel):
    order_id: UUID4
    product_url: HttpUrl

    @model_validator(mode="before")
    def add_url(self):
        product_id = self.product_id
        app_info = app.main.app

        url = (
            f"{app_info.servers[0].get('url')}/api/{app_info.version}/"
            f"products/{product_id}/"
        )
        self.__dict__["product_url"] = url
        return self


class OrderInUserResponse(OrderBase):
    order_id: UUID4
    quantity: int


class Order(OrderBase, models.Timestamp):
    """
    Represents the public schema for an order.
    """


class OrderPublic(BaseResponse[Order]):
    """
    Represents the public schema for an order.
    """

    message: str = "Order retrieved successfully"
    status_code: int = status.HTTP_200_OK
    data: Order


class OrdersPublic(BaseResponse[Order]):
    """
    Represents a list of public orders.
    """

    message: str = "Orders retrieved successfully"
    status_code: int = status.HTTP_200_OK
    data: list[Order]


class OrdersInUserResponse(BaseResponse[OrderInUserResponse]):
    """
    Represents a list of orders in a user response.
    """

    message: str = "User orders retrieved successfully."
    status_code: int = status.HTTP_200_OK
    count: int
    data: list[OrderInUserResponse]


class ImageResponse(SQLModel):
    """
    Represents the schema for an image response.
    """

    file_path: str
    image_id: UUID


class TokenBase(SQLModel):
    """
    Represents the schema for a token.
    """

    access_token: str
    token_type: str = "bearer"
    expires: datetime


class Token(BaseResponse[TokenBase]):
    """
    Represents the schema for a token.
    """

    message: str = "Token created successfully."
    status_code: int = status.HTTP_201_CREATED
    data: TokenBase


class TokenPayload(SQLModel):
    """
    Represents the payload of a token.
    """

    user_id: UUID4
    email: EmailStr


class Status(SQLModel):
    """
    Represents the schema for a status.
    """

    status: str
    version: str
    title: str
    servers: list[dict[str, str]]


class StatusResponse(BaseResponse[Status]):
    """
    Represents the schema for a status response.
    """

    message: str = "TinyCart API is running."
    status_code: int = status.HTTP_200_OK
    data: Status
