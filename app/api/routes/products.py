from uuid import UUID

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app import schemas, utils
from app.api import CurrentUserDependency, UserDependency
from app.core.deps import DBSessionDependency, PaginationLimitDependency
from app.crud.products import crud_product

router = APIRouter(dependencies=[UserDependency])


@router.post(
    "",
    response_model=schemas.ProductPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new product",
)
async def create_product(
    db: DBSessionDependency,
    user: CurrentUserDependency,
    name: str = Form(...),
    description: str = Form(...),
    unit_price: float = Form(...),
    images: list[UploadFile] = File(...),
    in_stock: bool = Form(...),
    number_in_stock: int = Form(...),
):
    """
    Creates a new product.

    This endpoint allows authenticated users with the role of `seller` to
    create a new product by providing its details. The product's information,
    including name, description, unit price, stock status, and number in
    stock, is submitted through form data. Images for the product can be
    uploaded as files.

    An error is encountered If the current user's role is not `seller`,
    indicating they are not authorized to create a product. This operation
    requires the user to be authenticated and authorized as a `seller`.
    """
    if user.role != "seller":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to perform this action.",
        )

    product = schemas.ProductCreate(
        name=name,
        description=description,
        unit_price=unit_price,
        in_stock=in_stock,
        number_in_stock=number_in_stock,
        product_owner_id=user.user_id,
    )

    image_paths = [utils.save_image(image) for image in images]
    product = crud_product.create(
        db=db,
        product=product,
        image_paths=image_paths,
    )

    return {
        "data": product,
        "message": "Product created successfully.",
        "status_code": status.HTTP_201_CREATED,
    }


@router.get(
    "",
    response_model=schemas.ProductsPublic,
    summary="Retrieve all products",
)
async def get_products(
    db: DBSessionDependency,
    skip: int = 0,
    limit: int = PaginationLimitDependency,
):
    """
    Retrieves all products with pagination.

    This authenticated endpoint provides a list of all products available in
    the database for authenticated users. It supports pagination through
    `skip` and `limit` query parameters, allowing clients to fetch products
    in manageable chunks.
    """
    products = crud_product.get_all(db=db, skip=skip, limit=limit)
    return {"data": products}


@router.get(
    "/{product_id}",
    response_model=schemas.ProductPublic,
    summary="Retrieve a product by ID",
)
async def get_product(product_id: UUID, db: DBSessionDependency):
    """
    Retrieve a product by its unique identifier (UUID).

    This authenticated endpoint allows users to retrieve detailed information
    about a specific product by providing its unique identifier (UUID). The
    product's details, including name, description, unit price, and stock
    status, are returned.

    This operation requires user authentication. Only authenticated users can
    access the detailed information of a specific product. It is designed to
    provide users with detailed information about a product they may be
    interested in purchasing or learning more about.
    """
    return {"data": crud_product.get_by_id(product_id=product_id, db=db)}


@router.put(
    "/{product_id}",
    response_model=schemas.ProductPublic,
    summary="Update a product",
)
async def update_product(
    db: DBSessionDependency,
    owner: CurrentUserDependency,
    product_id: UUID,
    name: str = Form(None),
    description: str = Form(None),
    unit_price: float = Form(None),
    in_stock: bool = Form(None),
    number_in_stock: int = Form(None),
    images: list[UploadFile] = File(None),
):
    """
    Updates an existing product in the database.

    This authenticated endpoint allows users with the role of `seller` to
    update the details of an existing product by providing its unique
    identifier (UUID) and the new values for its attributes. The product's
    name, description, unit price, stock status, and number in stock can be
    updated. Additionally, new images for the product can be uploaded.

    This operation requires user authentication and authorization as the
    product's owner. It involves updating the product's details in the
    database and optionally saving new images, returning the updated
    product's details upon success.
    """
    params = {
        "name": name,
        "description": description,
        "unit_price": unit_price,
        "in_stock": in_stock,
        "product_owner_id": owner.user_id,
        "number_in_stock": number_in_stock,
    }

    filtered_params = {k: v for k, v in params.items() if v is not None}

    product = schemas.ProductUpdate(**filtered_params)
    image_paths = (
        [utils.save_image(image) for image in images] if images else None
    )
    updated_product = crud_product.update(
        db=db, product=product, image_paths=image_paths, product_id=product_id
    )

    return {
        "message": "Product updated successfully",
        "status_code": status.HTTP_200_OK,
        "data": updated_product,
    }


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a product",
)
async def delete_product(
    product_id: UUID,
    current_user: CurrentUserDependency,
    db: DBSessionDependency,
):
    """
    Deletes an existing product from the database.

    This authenticated endpoint allows users with the role of 'seller' to
    delete a product by providing its unique identifier (UUID). The deletion
    process is performed in the context of the current user's session,
    ensuring that only the product's owner can delete it.

    This operation requires user authentication and authorization as the
    product's owner. It ensures that only authorized users can delete their
    products, maintaining data integrity and security.
    """
    return crud_product.delete(
        product_id=product_id, owner_id=current_user.user_id, db=db
    )


@router.get(
    "/{product_id}/orders",
    response_model=schemas.OrdersPublic,
    summary="Retrieve all orders for a product",
)
async def get_product_order(product_id: UUID, db: DBSessionDependency):
    """
    Retrieve all orders associated with a specific product.

    This authenticated endpoint allows users to retrieve a list of all orders
    associated with a specific product by providing the product's unique
    identifier (UUID). It is particularly useful for sellers who wish to track
    the sales of their products.

    This operation requires user authentication. It is designed to provide
    sellers with detailed information about the orders for their products,
    facilitating order management and fulfillment.
    """
    product_orders = crud_product.get_orders(product_id=product_id, db=db)

    return {"data": product_orders}
