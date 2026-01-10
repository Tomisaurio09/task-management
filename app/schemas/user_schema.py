
#el user solo nos tiene que dar el email, password y el full name para el register
#para el login solo email y password

from pydantic import BaseModel, EmailStr, field_validator
from typing import Union
import re
class UserRegisterSchema(BaseModel):
    email: EmailStr
    password: Union[str, int]
    full_name: str

    @field_validator('full_name')
    @classmethod
    def validate_name(cls, full_name: str):
        pattern = r"^[A-Za-zÀ-ÿ\s'-]+$" 
        if re.match(pattern, full_name):
            return full_name
        raise ValueError("Invalid full name.")


    @field_validator('full_name')
    @classmethod
    def validate_name_length(cls, full_name):
        if len(full_name) <= 64:
            return full_name
        raise ValueError("Your full name must be 64 characters maximum.")
    
    @field_validator('password')
    @classmethod
    def validate_password_length(cls, password):
        if isinstance(password, (str, int)) and len(str(password)) >= 8:
            return password
        raise ValueError("Your password must be at least 8 characters long.")
    
