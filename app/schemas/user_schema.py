
#el user solo nos tiene que dar el email, password y el full name para el register
#para el login solo email y password

from pydantic import BaseModel, EmailStr, field_validator
from typing import Union

class UserRegisterSchema(BaseModel):
    email: EmailStr
    password: Union[str, int]
    full_name: str

    @field_validator('full_name')
    @classmethod
    def validate_name(cls, full_name):
        if full_name.isalpha():
            return full_name
        raise ValueError(f"Your full must only have letters, you can't write '{full_name}'")

    @field_validator('full_name')
    @classmethod
    def validate_name_length(cls, full_name):
        if full_name.isalpha() and len(full_name) <= 15:
            return full_name
        raise ValueError("Your full name must be 15 characters maximum.")
    
    @field_validator('password')
    @classmethod
    def validate_password_length(cls, password):
        if isinstance(password, (str, int)) and len(str(password)) >= 8:
            return password
        raise ValueError("Your password must be at least 8 characters long.")
    
class UserLoginSchema(BaseModel):
    email: EmailStr
    password: Union[str, int]