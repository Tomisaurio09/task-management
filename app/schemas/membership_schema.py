# app/schemas/membership_schema.py
from pydantic import BaseModel
from app.models.membership import UserRole

class AddMemberSchema(BaseModel):
    role: UserRole   

    class Config:
        from_attributes = True

class ChangeRoleMemberSchema(BaseModel):
    role: UserRole   

    class Config:
        from_attributes = True
