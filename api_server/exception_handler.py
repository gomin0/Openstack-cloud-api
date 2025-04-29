from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.orm.exc import StaleDataError

from common.exception.base_exception import CustomException


async def custom_validation_error_handler(request: Request, exc: RequestValidationError):
    errors = []
    for err in exc.errors():
        field = ".".join(str(loc) for loc in err["loc"])
        errors.append({
            "field": field,
            "message": err["msg"],
            "type": err["type"],
        })

    return JSONResponse(
        status_code=422,
        content={
            "code": "VALIDATION_FAILED",
            "message": "Validation Failed",
            "errors": errors
        }
    )


async def custom_exception_handler(request: Request, exc: CustomException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.code,
            "message": exc.message,
        },
    )


async def stale_data_error_handler(request: Request, exc: StaleDataError):
    return JSONResponse(
        status_code=409,
        content={
            "code": "OPTIMISTIC_LOCK_CONFLICT",
            "message": "다른 사용자가 데이터를 수정하여 요청하신 내용을 처리할 수 없습니다. 잠시 후 다시 시도해주세요."
        },
    )
