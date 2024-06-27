from fastapi import APIRouter

from app.api.routes import orders, products, users, auth

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(
    products.router, prefix="/products", tags=["products"]
)
api_router.include_router(orders.router, prefix="/orders", tags=["orders"])
api_router.include_router(auth.router, tags=["authentication"])
