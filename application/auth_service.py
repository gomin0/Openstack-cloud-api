import asyncio

import bcrypt
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from domain.user.entitiy import User
from exception.auth_exception import InvalidAuthException
from infrastructure.database import transactional
from infrastructure.user.repository import UserRepository


class AuthService:
    encoding: str = "UTF-8"

    def __init__(self, user_repository: UserRepository = Depends()):
        self.user_repository = user_repository

    @transactional()
    async def authenticate_user(
        self,
        session: AsyncSession,
        account_id: str,
        password: str,
    ) -> User:
        user: User | None = await self.user_repository.find_by_account_id(
            session=session,
            account_id=account_id,
            with_relations=True,
        )
        if user is None:
            raise InvalidAuthException()

        is_valid_password: bool = await asyncio.to_thread(
            bcrypt.checkpw,
            password=password.encode(self.encoding),
            hashed_password=user.password.encode(self.encoding)
        )
        if not is_valid_password:
            raise InvalidAuthException()

        return user
