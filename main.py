from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.responses import JSONResponse
from exception.base_exceptions import CustomException, custom_validation_error_handler
from router import user_router

app = FastAPI()

app.add_exception_handler(RequestValidationError, custom_validation_error_handler)

app.include_router(user_router.router)


@app.exception_handler(CustomException)
async def custom_exception_handler(request: Request, exc: CustomException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.code,
            "message": exc.message,
        },
    )