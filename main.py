from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from exception.base_exception import CustomException
from exception.exception_handler import custom_validation_error_handler, custom_exception_handler
from router import user_router

app = FastAPI()

app.add_exception_handler(RequestValidationError, custom_validation_error_handler)
app.add_exception_handler(CustomException, custom_exception_handler)

app.include_router(user_router.router)