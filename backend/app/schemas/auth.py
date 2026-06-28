from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=128)


class LoginRequest(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    is_admin: bool
    ntfy_topic: str | None
    digest_hour: int
    digest_minute: int
    digest_evening_hour: int
    digest_evening_minute: int
    timezone: str
    feed_window_hours: int
    onboarded: bool
    personalized_feed: bool = True

    model_config = {"from_attributes": True}


class AuthConfigResponse(BaseModel):
    allow_registration: bool


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=6, max_length=128)
