from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from mealroulette.api.routes.health import router as health_router
from mealroulette.core.config import settings
from mealroulette.core.errors import http_exception_handler, validation_exception_handler
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError


def create_app() -> FastAPI:
    app = FastAPI(title="MealRoulette", version="0.1.0", debug=settings.debug)

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

    return app


app = create_app()
