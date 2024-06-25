from typing import List

from sqlalchemy import Column, DateTime, Integer, String, func, select, desc, delete
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import relationship

from db.postgres import Base, async_session
from pydantic import BaseModel
from decorators.as_dict import AsDict
from decorators.db_session import db_session


class MRole(BaseModel):
    name: str
    description: str
    custom_instructions: str
    created_by: str
    permissions: dict = None


class Role(Base, AsDict):
    __tablename__ = 'role'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    description = Column(String, nullable=True)
    custom_instructions = Column(String, nullable=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


    def as_dict(self):
        return {
                'id': self.id,
                'name': self.name,
                'description': self.description,
                'custom_instructions': self.custom_instructions,
                'created_by': self.created_by
            }


class RoleStore:
    @staticmethod
    @db_session
    async def choose_name(session, name: str):
        index = 1
        all_roles_name = [role.name for role in (await RoleStore.get_all_roles())]
        while f'{name} {index}' in all_roles_name:
            index += 1
            name = f'{name} {index}'
        return name

    @staticmethod
    @db_session
    async def create_role(session, name: str = None, description: str = None, custom_instructions: str = None,
                          created_by: str = None):
        name = await RoleStore.choose_name(name)
        role = Role(name=name, description=description, custom_instructions=custom_instructions, created_by=created_by)
        session.add(role)
        await session.commit()

        return role

    @staticmethod
    @db_session
    async def get_by_name(session, name: str):
        role_result = await session.execute(select(Role).where(Role.name == name))
        role = role_result.scalar()

        return role

    @staticmethod
    @db_session
    async def get_role_by_id(session, role_id: int):
        role_result = await session.execute(select(Role).where(Role.id == role_id))
        role = role_result.scalar()

        return role

    @staticmethod
    @db_session
    async def get_all_roles(session):
        roles = await session.execute(select(Role).order_by(Role.created_at))
        return roles.scalars().all()

    @staticmethod
    @db_session
    async def attach_role_to_user(session, role: Role, user):
        user.role = role
        session.add(user)
        await session.commit()

    @staticmethod
    @db_session
    async def get_all(session, search_term: str = None) -> List[Role]:
        query = select(Role)

        if search_term:
            search_expression = f"%{search_term}%"
            query = query.where(Role.name.ilike(search_expression))

        result = await session.execute(query)
        results = result.scalars().all()

        return results

    @staticmethod
    @db_session
    async def delete(session, role_id: int):

        await session.execute(
            delete(Role).where(Role.id == role_id)
        )
        await session.commit()

    @staticmethod
    @db_session
    async def update(session, role_id: int, data: dict):
        role = (await session.execute(select(Role).filter_by(id=role_id))).scalar()

        if role is None:
            return None

        for field, value in data.items():
            setattr(role, field, value)

        await session.commit()
        return role