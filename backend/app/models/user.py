from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator

OnboardingStep = Literal["upload", "provider", "token", "done"]
AuthMode = Literal["native", "hf_inference_providers"]
ProviderId = Literal["groq", "cerebras", "huggingface"]


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
    has_credential: bool
    next_step: OnboardingStep


class UserOut(BaseModel):
    id: str
    email: str
    created_at: datetime
    onboarding_completed: bool
    has_credential: bool
    token_masked: str | None
    selected_provider: str | None
    selected_model: str | None
    auth_mode: str | None
    onboarding: OnboardingState


class AuthOut(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    user: UserOut


class CredentialIn(BaseModel):
    provider: str = Field(min_length=1, max_length=64)
    auth_mode: AuthMode
    token: str = Field(min_length=8, max_length=256)
    model: str = Field(min_length=1, max_length=200)

    @field_validator("token")
    @classmethod
    def no_spaces(cls, value: str) -> str:
        value = value.strip()
        if any(c.isspace() for c in value):
            raise ValueError("API keys cannot contain spaces")
        return value


class CredentialActiveIn(BaseModel):
    provider: str = Field(min_length=1, max_length=64)


class CredentialOut(BaseModel):
    provider: str
    auth_mode: str
    model: str
    token_masked: str | None
    is_active: bool
    added_at: datetime
