# app/schemas/membership_schema.py
from pydantic import BaseModel
from app.models.membership import UserRole
from uuid import UUID
class AddMemberSchema(BaseModel):
    role: UserRole   

    class Config:
        from_attributes = True

class ChangeRoleMemberSchema(BaseModel):
    role: UserRole   

    class Config:
        from_attributes = True

class MemberResponseSchema(BaseModel):
    user_id: UUID
    role: UserRole
    invited_by: UUID | None
    class Config:
        from_attributes = True