# app/schemas/membership_schema.py
from pydantic import BaseModel, ConfigDict
from app.models.membership import UserRole
from uuid import UUID
class AddMemberSchema(BaseModel):
    role: UserRole   

class ChangeRoleMemberSchema(BaseModel):
    role: UserRole   

class MemberResponseSchema(BaseModel):
    user_id: UUID
    role: UserRole
    invited_by: UUID | None
    model_config = ConfigDict(from_attributes=True)