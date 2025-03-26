from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi import Request
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

from exception.base_exception import CustomException


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
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "code":"VALIDATION_FAILED",
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