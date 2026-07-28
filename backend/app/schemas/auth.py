from pydantic import BaseModel, EmailStr


class SignupRequest(BaseModel):
    full_name: str
    email: EmailStr
    phone: str | None = None
    password: str
    confirm_password: str
    village: str | None = None
    district: str | None = None
    state: str | None = None
    role: str = 'farmer'
    admin_secret_key: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = False


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = 'bearer'
    role: str
    email: str
