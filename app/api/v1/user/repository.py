from typing import Optional

from sqlalchemy import select, insert, update, delete
from sqlalchemy.orm import joinedload

from core.db.db import database
from .models import UserModel, RoleModel, user_roles_table
from .schemas.requests import UserCreateSchema
from .schemas.exceptions import UserNotFoundException
from .schemas.responses import UserResponse


class UserRepository:
    def __init__(self, db=database):
        self.db = db

    async def create_user(self, user: UserCreateSchema):
        try:
            # Start transaction by rolling back the session
            await self.db.rollback()

            user_dict = user.dict()
            role_name = user.role
            del user_dict["role"]

            # Insert user into database
            query = insert(UserModel).values(**user_dict)
            user = await self.db.execute(query)

            # Retrieve role by name
            query = select(RoleModel).where(RoleModel.role == role_name)
            role = await self.db.execute(query)
            role = role.scalars().first()

            if role:
                # Link the user with the role
                query = insert(user_roles_table).values({'role_id': role.id, 'user_id': user.inserted_primary_key[0]})
                await self.db.execute(query)

            # Commit transaction
            await self.db.commit()

            return await self.get_user_by_id(user.inserted_primary_key[0])
        except Exception as e:
            await self.db.rollback()
            raise Exception(f"Error creating user: {str(e)}")

    async def get_user_by_email(self, email: str):
        try:
            await self.db.rollback()
            query = select(UserModel).where(UserModel.email == email).options(joinedload(UserModel.roles))
            result = await self.db.execute(query)
            user = result.scalars().first()
            return user
        except Exception as e:
            raise Exception(f"Error fetching user by email: {str(e)}")

    async def get_user_by_id(self, user_id: int):
        try:
            await self.db.rollback()
            query = select(UserModel).where(UserModel.id == user_id).options(joinedload(UserModel.roles))
            result = await self.db.execute(query)
            user = result.scalars().first()
            if not user:
                raise UserNotFoundException
            return user
        except Exception as e:
            raise Exception(f"Error fetching user by ID: {str(e)}")

    async def get_user_list(self, limit: int = 12, prev: Optional[int] = None):
        try:
            query = select(UserModel)

            if prev:
                query = query.where(UserModel.id < prev)

            query = query.options(joinedload(UserModel.roles)).limit(limit)

            result = await self.db.execute(query)
            users = result.scalars().unique().all()

            return users
        except Exception as e:
            raise Exception(f"Error fetching user list: {str(e)}")
