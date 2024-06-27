from fastapi import APIRouter, status
from pydantic import UUID4

from app import schemas
from app.api import CurrentUserDependency, UserDependency
from app.core import deps
from app.crud.users import crud_user

router = APIRouter()


@router.post(
    "",
    response_model=schemas.UserPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
)
async def create_user(user: schemas.UserCreate, db: deps.DBSessionDependency):
    """
    This endpoint allows you create a user to interact with the system. You
    have two options:

    - **Create a buyer user.**
    - **Create a seller user.**

    If you create a buyer user, you can only buy products. If you create a
    seller user, you can sell and buy products. You specify the user type by
    the `role` field in the request body. Simply provide `seller` or `buyer`
    when creating the user.

    **Note**: The `role` can be updated after user creation to accommodate for
    users whose user type is a `buyer` and would like to upgrade to `seller`.
    The converse is also true for users who are already of type `seller` to
    downgrade to a `buyer`.
    """
    user = crud_user.create(db=db, user=user)
    return {
        "data": user,
        "status_code": status.HTTP_201_CREATED,
        "message": "User created successfully",
    }


@router.get(
    "",
    response_model=schemas.UsersPublic | schemas.UserPublic,
    dependencies=[UserDependency],
    summary="Retrieve users on the platform",
)
async def get_users(
    *,
    db: deps.DBSessionDependency,
    skip: int = 0,
    limit: int = deps.PaginationLimitDependency,
    username: str = None,
    email: str = None,
):
    """
    This endpoint retrieves a list of users or a specific user from the system
    based on the provided search criteria. You have the flexibility to search
    for users by their `username` or `email`. This allows for a more targeted
    retrieval of user information, catering to different needs:

    - **Search by Username**: If you are looking for a specific user and know
      their username, you can provide it as a query parameter. This will
      return the public information of the user associated with the given
      username.

    - **Search by Email**: Similarly, if you have the email of the user, you
      can use it as a search criterion. This is particularly useful in
      scenarios where usernames might be forgotten or not known, but the
      email address is available.

    If no search parameters (`username` or `email`) are provided, the endpoint
    will return a paginated list of all users in the system. This is useful
    for getting an overview of all users or for administrative purposes where
    a comprehensive list is required.

    This endpoint also supports pagination through the `skip` and `limit`
    query parameters, allowing you to control the number of users returned in
    the list and to paginate through large sets of users efficiently.

    **Note**: This endpoint is designed with privacy in mind, ensuring that
    sensitive user information is not exposed. It is suitable for both
    administrative use and functionality within the application that requires
    user lookup capabilities.
    """
    if username:
        user = crud_user.get(by="username", identifier=username, db=db)
        return schemas.UserPublic(data=user)

    if email:
        user = crud_user.get(by="email", identifier=email, db=db)
        return schemas.UserPublic(data=user)

    return {"data": crud_user.get_all(db=db, skip=skip, limit=limit)}


@router.get(
    "/me", response_model=schemas.UserPublic, summary="Retrieve current user"
)
async def get_me(user: CurrentUserDependency):
    """
    This endpoint is dedicated to retrieving the profile information of the
    currently authenticated user. It serves as a personal endpoint for users
    to access their own information within the system.

    Upon successful authentication, the endpoint returns the profile details
    of the user making the request. This ensures that any sensitive or private
    user information is appropriately safeguarded while still providing users
    with access to their own data.

    The endpoint is particularly useful for user profile pages or settings
    where users need to view or update their information. It supports
    scenarios where understanding the context of the current user is crucial,
    such as personalized user experiences, dashboard displays, or when
    performing actions that require user identity verification.
    """
    return {"data": user}


@router.get(
    "/me/products",
    response_model=schemas.ProductsInUserResponse,
    tags=["products"],
    summary="Retrieve products created by the current user",
)
def get_my_products(
    user: CurrentUserDependency,
    db: deps.DBSessionDependency,
    skip: int = 0,
    limit: int = deps.PaginationLimitDependency,
):
    """
    This endpoint allows the current authenticated user to retrieve a list of
    products they have created. It's designed to enable users to easily manage
    and view their own products within the system.

    This endpoint is particularly useful for users who are `sellers`
    on the platform, providing them with a quick and efficient way to access
    all products they've listed. It supports pagination through the `skip` and
    `limit` parameters, allowing for scalable and user-friendly navigation
    through potentially large product catalogs.
    """
    products = crud_user.get_products(
        db=db, user_id=user.user_id, skip=skip, limit=limit
    )
    return {"data": products}


@router.get(
    "/me/orders",
    response_model=schemas.OrdersInUserResponse,
    tags=["orders"],
    summary="Retrieve orders made by the current user",
)
async def get_current_user_orders(
    db: deps.DBSessionDependency,
    user: CurrentUserDependency,
    skip: int = 0,
    limit: int = deps.PaginationLimitDependency,
):
    """
    This endpoint is tailored for the current authenticated user to retrieve a
    list of their orders. It provides a personalized view into the orders that
    the user has placed, facilitating easy tracking and management of their
    purchase history.

    This endpoint is especially useful for users who wish to review their past
    orders, check the status of current orders, or simply have a consolidated
    view of their purchasing history on the platform. It supports pagination,
    allowing users to navigate through their orders efficiently, regardless of
    the total number of orders they have placed.

    **Note**: This endpoint is usable by both `buyer` and `seller` users, as
    it provides a comprehensive view of all orders associated with the user.
    """
    return {
        "data": crud_user.get_orders(
            db=db, user_id=user.user_id, skip=skip, limit=limit
        )
    }


@router.get(
    "/{user_id}",
    response_model=schemas.UserPublic,
    dependencies=[UserDependency],
    summary="Retrieve a specific user by ID",
)
async def get_user(
    db: deps.DBSessionDependency,
    user_id: UUID4 = deps.UserIdDependency,
):
    """
    This endpoint is designed to retrieve detailed information about a
    specific user by their unique identifier (ID). It is primarily intended
    for administrative use or for functionalities within the application that
    require detailed user information.

    Upon receiving a valid request, the endpoint queries the database for a
    user with the specified `user_id`. If found, it returns the user's
    information. If the user is not found, the endpoint returns a `404 Not
    Found` error, indicating that the user with the given ID does not exist.

    This endpoint is crucial for operations that require fetching user details
    based on their ID, such as viewing profiles, administrative tasks, or
    supporting user-related queries where direct identification is necessary.
    """
    return {"data": crud_user.get(by="id", db=db, identifier=user_id)}


@router.put(
    "/me", response_model=schemas.UserPublic, summary="Update current user"
)
async def update_current_user(
    current_user: CurrentUserDependency,
    user_data: schemas.UserUpdate,
    db: deps.DBSessionDependency,
):
    """
    This endpoint is dedicated to allowing the current authenticated user to
    update their own profile information. It provides a secure and
    user-friendly way for users to make changes to their personal details,
    ensuring that their profile remains up-to-date.

    This endpoint is crucial for maintaining user engagement and satisfaction,
    as it empowers users with control over their personal information,
    enhancing their overall experience with the application.
    """
    user = crud_user.update(
        db=db,
        schema=user_data,
        obj_id=current_user.user_id,
        obj_owner_id=current_user.user_id,
    )

    return {
        "data": user,
        "message": "User updated successfully",
        "status_code": status.HTTP_200_OK,
    }


@router.put(
    "/{user_id}",
    response_model=schemas.UserPublic,
    summary="Update a user by ID",
)
async def update_user(
    current_user: CurrentUserDependency,
    user_data: schemas.UserUpdate,
    db: deps.DBSessionDependency,
    user_id: UUID4 = deps.UserIdDependency,
):
    """
    Updates a user's information based on the provided user ID and update data.

    This endpoint allows for the modification of a user's details in the
    database. It is secured to ensure that only authenticated users can update
    user information, and further, that users can only update their own
    information unless they have administrative privileges.

    The function first attempts to update the user's information in the
    database using the provided `user_id` and `user_data`. If successful, it
    returns a JSON response containing the updated user information, a success
    message, and the HTTP status code 200 OK.
    """
    user = crud_user.update(
        db=db,
        schema=user_data,
        obj_id=user_id,
        obj_owner_id=current_user.user_id,
    )

    return {
        "data": user,
        "message": "User updated successfully",
        "status_code": status.HTTP_200_OK,
    }


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete current user",
)
async def delete_current_user(
    db: deps.DBSessionDependency,
    current_user: CurrentUserDependency,
):
    """
    Deletes the current user's account from the system.

    This endpoint is designed to allow authenticated users to delete their own
    account. It ensures that the operation is secure and that only the account
    owner can initiate and complete the deletion process.
    """
    return crud_user.delete(
        db=db, obj_id=current_user.user_id, obj_owner_id=current_user.user_id
    )


@router.delete("/{user_id}", status_code=204, summary="Delete a user by ID")
async def delete_user(
    user_id: UUID4,
    db: deps.DBSessionDependency,
    current_user: CurrentUserDependency,
):
    """
    Deletes a user account by user ID.

    This endpoint facilitates the deletion of a user account from the
    database, identified by its unique user ID. It is designed to ensure that
    only authorized users, such as administrators or the users themselves, can
    delete user accounts.

    An error will be thrown when any of the following conditions are met:
    - the user is not found
    - the current user does not have the rights to delete the account
    - any other error occurs during the deletion process.
    """
    return crud_user.delete(
        db=db, obj_id=user_id, obj_owner_id=current_user.user_id
    )


@router.get(
    "/{user_id}/orders",
    response_model=schemas.OrdersInUserResponse,
    dependencies=[UserDependency],
    summary="Retrieve orders made by a specific user",
    tags=["orders"],
)
async def get_user_orders(
    db: deps.DBSessionDependency,
    user_id: UUID4 = deps.UserIdDependency,
    skip: int = 0,
    limit: int = deps.PaginationLimitDependency,
):
    """
    Retrieves all orders made by a specific user.

    This endpoint is designed to fetch a list of orders placed by a specific
    user, identified by their unique user ID. It ensures data privacy and
    integrity by allowing only authorized access to user order information.
    """
    return {
        "data": crud_user.get_orders(
            db=db, user_id=user_id, skip=skip, limit=limit
        )
    }


@router.get(
    "/{user_id}/products",
    response_model=schemas.ProductsInUserResponse,
    dependencies=[UserDependency],
    summary="Retrieve products created by a specific user",
    tags=["products"],
)
async def get_user_products(
    db: deps.DBSessionDependency,
    user_id: UUID4 = deps.UserIdDependency,
    skip: int = 0,
    limit: int = deps.PaginationLimitDependency,
):
    """
    Retrieve products created by a specific user.

    This endpoint fetches a list of products that have been created by a
    specific user, identified by their unique user ID. It is designed to
    support scenarios where users can create, list, and manage their own
    products within the platform.

    The function executes a database query through `crud_user.get_products`,
    passing in the database session (`db`) and the user ID (`user_id`). This
    function is responsible for fetching all products that have been created
    by the specified user from the database.

    If any error occurs during the database query process or if the user ID
    does not exist in the database, an error will be encountered and returned
    to the user.
    """
    result = crud_user.get_products(
        db=db, user_id=user_id, skip=skip, limit=limit
    )
    return {"data": result}
