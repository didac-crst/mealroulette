from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from mealroulette.api.routes.auth import router as auth_router
from mealroulette.api.routes.backup import router as backup_router
from mealroulette.api.routes.catalog import router as catalog_router
from mealroulette.api.routes.cooking import router as cooking_router
from mealroulette.api.routes.health import router as health_router
from mealroulette.api.routes.planning import router as planning_router
from mealroulette.api.routes.scheduler import router as scheduler_router
from mealroulette.api.routes.shopping import router as shopping_router
from mealroulette.api.routes.taxonomy import router as taxonomy_router
from mealroulette.api.routes.telegram import router as telegram_router
from mealroulette.api.routes.users import router as users_router
from mealroulette.core.config import settings
from mealroulette.core.errors import http_exception_handler, validation_exception_handler
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError


def create_app() -> FastAPI:
    app = FastAPI(
        title="MealRoulette",
        version="0.1.0",
        debug=settings.debug,
        description=(
            "API docs: click **Authorize**, enter your username and password, then call protected "
            "endpoints. `/api/auth/login` returns tokens but does not attach them automatically; "
            "use **Authorize** or `POST /api/auth/token`. `/api/auth/refresh` requires "
            "`refresh_token` (not `access_token`) and rotates the refresh token on each use."
        ),
        swagger_ui_parameters={
            "tryItOutEnabled": True,
            "persistAuthorization": True,
        },
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    app.include_router(health_router, prefix="/api")
    app.include_router(auth_router, prefix="/api")
    app.include_router(catalog_router, prefix="/api")
    app.include_router(backup_router, prefix="/api")
    app.include_router(cooking_router, prefix="/api")
    app.include_router(planning_router, prefix="/api")
    app.include_router(shopping_router, prefix="/api")
    app.include_router(scheduler_router, prefix="/api")
    app.include_router(taxonomy_router, prefix="/api")
    app.include_router(telegram_router, prefix="/api")
    app.include_router(users_router, prefix="/api")

    return app


app = create_app()
