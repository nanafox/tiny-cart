from uuid import UUID

from fastapi import APIRouter, status

from app import schemas
from app.api import CurrentUserDependency, UserDependency
from app.core.deps import DBSessionDependency, PaginationLimitDependency
from app.crud.orders import crud_order

router = APIRouter(dependencies=[UserDependency])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=schemas.OrderPublic,
    summary="Create a new order",
)
async def create_order(
    order: schemas.OrderCreate,
    current_user: CurrentUserDependency,
    db: DBSessionDependency,
):
    """
    Creates a new order for the current user.

    This endpoint is responsible for creating a new order based on the
    provided order details. It ensures that only authenticated users can
    create orders and that the orders are associated with their account.

    An order can be created with one or more products, each with a specified
    quantity. The endpoint validates the product availability and quantity to
    ensure that the order can be fulfilled successfully. If the order is
    valid, it is created and stored in the database.
    """
    order = await crud_order.create(
        db=db, order=order, user_id=current_user.user_id
    )
    return {
        "data": order,
        "message": "Order created successfully",
        "status_code": status.HTTP_201_CREATED,
    }


@router.get(
    "",
    response_model=schemas.OrdersPublic,
    summary="Retrieve all orders",
    tags=["orders"],
)
async def get_orders(
    db: DBSessionDependency,
    skip: int = 0,
    limit: int = PaginationLimitDependency,
):
    """
    Retrieve all orders with optional pagination.

    This endpoint fetches a list of all orders placed within the system, with
    support for pagination through `skip` and `limit` parameters. It is
    designed to provide a comprehensive view of orders for administrative
    purposes or for users with the appropriate permissions.

    Omitting the `skip` and `limit` will return the first 10 orders by default.
    """
    orders = crud_order.get_all(db=db, skip=skip, limit=limit)

    return {"data": orders}


@router.get(
    "/{order_id}",
    response_model=schemas.OrderPublic,
    summary="Retrieve a single order",
)
async def get_order(order_id: UUID, db: DBSessionDependency):
    """
    Retrieve a single order by its unique order ID.

    This endpoint is designed to fetch detailed information about a specific
    order, identified by its unique order ID. It ensures that only authorized
    users can access order details, typically the user who placed the order or
    users with administrative privileges.

    An error is encountered if the order is not found in the database or if
    any error occurs during the database query process.
    """
    return {"data": crud_order.get_by_id(order_id=order_id, db=db)}


@router.put(
    "/{order_id}",
    response_model=schemas.OrderPublic,
    summary="Update an order",
)
async def update_order(
    order_id: UUID,
    orders: schemas.OrderUpdate,
    current_user: CurrentUserDependency,
    db: DBSessionDependency,
):
    """
    Updates an existing order.

    This endpoint allows for the modification of an existing order, identified
    by its unique order ID. It ensures that only the user who placed the order
    or users with administrative privileges can update the order details.

    This request would update the specified order with the new items and
    instructions provided in the request body.
    """
    order = crud_order.update(
        order_id=order_id, orders=orders, user_id=current_user.user_id, db=db
    )

    return {
        "data": order,
        "message": "Order updated successfully",
        "status_code": status.HTTP_200_OK,
    }


@router.delete(
    "/{order_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an order",
)
async def delete_order(
    order_id: UUID,
    db: DBSessionDependency,
    current_user: CurrentUserDependency,
):
    """
    Deletes an existing order from the database.

    This endpoint allows users to delete an order by specifying its unique
    identifier (UUID). The deletion process is performed in the context of the
    current user's session, ensuring that only authorized users can delete
    orders they have access to.

    Where `{order_id}` is the UUID of the order to be deleted.
    """
    return crud_order.delete(
        order_id=order_id, db=db, user_id=current_user.user_id
    )
