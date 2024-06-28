from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse

from app import schemas
from app.api.main import api_router
from app.core.settings import settings

description = """
TinyCart API is a simple mini-shop API. It allows you to manage users,
products, and orders. You can create, read, update, and delete users and
products. You can also create orders for a user with a product and a quantity.

The API is organized around REST. It has predictable resource-oriented URLs,
accepts form-encoded request bodies, returns JSON-encoded responses, and uses
standard HTTP response codes, authentication, and verbs. It also uses the
OpenAPI standard to describe its API.
"""

if settings.dev:
    servers = [
        {"url": "http://localhost:8000", "description": "Local server"}
    ]
else:
    servers = [{"url": settings.prod_url, "description": "Production server"}]


app = FastAPI(
    title="TinyCart API",
    version=settings.api_version,
    description=description,
    contact={
        "name": "Maxwell Nana Forson",
        "url": "https://linktr.ee/theLazyProgrammer",
        "email": "nanaforsonjnr@gmail.com",
    },
    docs_url=f"/api/{settings.api_version}/docs" if settings.dev else None,
    redoc_url=f"/api/{settings.api_version}/redoc" if settings.dev else None,
    servers=servers,
)


origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@api_router.get("/schema", include_in_schema=False)
def get_api_schema():
    print("using this")
    return FileResponse(settings.api_schema_filepath)


@api_router.get("/docs", include_in_schema=False)
async def get_docs():
    return RedirectResponse(
        url="https://documenter.getpostman.com/view/14404907/2sA3dsnESD",
        status_code=status.HTTP_301_MOVED_PERMANENTLY,
    )


@api_router.get(
    "/status/",
    tags=["status"],
    response_model=schemas.StatusResponse,
    summary="API Status",
)
async def get_api_status():
    """Check the API status."""
    return {
        "data": {
            "status": "OK",
            "version": app.version,
            "title": app.title,
            "servers": servers,
        },
        "message": f"{app.title} is running",
        "status_code": 200,
    }


app.include_router(api_router)
