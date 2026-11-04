from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator

OnboardingStep = Literal["upload", "token", "provider", "done"]


class SignupIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Password cannot be only spaces")
        return value


class SigninIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class OnboardingState(BaseModel):
    has_document: bool
    has_token: bool
    has_provider: bool
    next_step: OnboardingStep


class UserOut(BaseModel):
    id: str
    email: str
    created_at: datetime
    onboarding_completed: bool
    has_hf_token: bool
    hf_token_masked: str | None
    selected_provider: str | None
    selected_model: str | None
    onboarding: OnboardingState


class AuthOut(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    user: UserOut


class HfTokenIn(BaseModel):
    token: str = Field(min_length=8, max_length=256)

    @field_validator("token")
    @classmethod
    def looks_like_hf_token(cls, value: str) -> str:
        value = value.strip()
        if not value.startswith("hf_") or any(c.isspace() for c in value):
            raise ValueError("Hugging Face tokens start with hf_ and contain no spaces")
        return value


class ProviderIn(BaseModel):
    provider: str = Field(min_length=1, max_length=64)
    model: str = Field(min_length=1, max_length=200)
