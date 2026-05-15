from pydantic import BaseModel


class TokenExchangeResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class StandardActionResponse(BaseModel):
    detail: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str
