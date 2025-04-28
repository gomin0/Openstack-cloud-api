from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm.exc import StaleDataError

from domain.server.entity import Server
from exception.base_exception import CustomException
from exception.exception_handler import (
    custom_validation_error_handler,
    custom_exception_handler,
    stale_data_error_handler,
)
from infrastructure.async_client import init_async_client, close_async_client
from router.auth.router import router as auth_router
from router.floating_ip.router import router as floating_ip_router
from router.project.router import router as project_router
from router.security_group.router import router as security_group_router
from router.user.router import router as user_router
from router.volume.router import router as volume_router

Server


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_async_client()
    yield
    await close_async_client()


app = FastAPI(lifespan=lifespan)

app.include_router(user_router)
app.include_router(auth_router)
app.include_router(project_router)
app.include_router(volume_router)
app.include_router(security_group_router)
app.include_router(floating_ip_router)

app.add_exception_handler(RequestValidationError, custom_validation_error_handler)
app.add_exception_handler(CustomException, custom_exception_handler)
app.add_exception_handler(StaleDataError, stale_data_error_handler)
