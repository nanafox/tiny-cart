from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

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

swagger_ui_parameters = {
    "filter": True,
    "docExpansion": "list",
    "configUrl": "/static/api.json",
}

app = FastAPI(
    title="TinyCart API",
    version=settings.api_version,
    description=description,
    servers=servers,
    docs_url=f"/api/{settings.api_version}/docs",
    redoc_url=f"/api/{settings.api_version}/redoc",
    swagger_ui_parameters=swagger_ui_parameters,
    openapi_url="/static/api.json",
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/favicon.ico", include_in_schema=False)
def get_image():
    return FileResponse("app/static/favicon.ico")


@app.get("/static/api.json", include_in_schema=False)
def get_p():
    print("using this")
    return FileResponse("app/static/api.json")


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
