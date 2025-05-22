from contextlib import asynccontextmanager
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm.exc import StaleDataError

from api_server.exception_handler import (
    custom_validation_error_handler, custom_exception_handler, stale_data_error_handler,
)
from api_server.router.auth.router import router as auth_router
from api_server.router.floating_ip.router import router as floating_ip_router
from api_server.router.network_interface.router import router as network_interface_router
from api_server.router.project.router import router as project_router
from api_server.router.security_group.router import router as security_group_router
from api_server.router.server.router import router as server_router
from api_server.router.user.router import router as user_router
from api_server.router.volume.router import router as volume_router
from common.exception.base_exception import CustomException
from common.infrastructure.async_client import init_async_client, close_async_client
from common.util.envs import get_envs, Envs
from common.util.system_token_manager import refresh_system_keystone_token

envs: Envs = get_envs()

scheduler: AsyncIOScheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_async_client()

    scheduler.add_job(
        func=refresh_system_keystone_token,
        trigger=IntervalTrigger(seconds=envs.REFRESH_INTERVAL_SECONDS_FOR_SYSTEM_KEYSTONE_TOKEN),
        next_run_time=datetime.now(timezone.utc),
        max_instances=1,
    )
    scheduler.start()

    yield

    scheduler.shutdown()

    await close_async_client()


app = FastAPI(lifespan=lifespan)

app.include_router(user_router)
app.include_router(auth_router)
app.include_router(project_router)
app.include_router(volume_router)
app.include_router(security_group_router)
app.include_router(floating_ip_router)
app.include_router(server_router)
app.include_router(network_interface_router)

app.add_exception_handler(RequestValidationError, custom_validation_error_handler)
app.add_exception_handler(CustomException, custom_exception_handler)
app.add_exception_handler(StaleDataError, stale_data_error_handler)
