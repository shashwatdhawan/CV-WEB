from pydantic import BaseModel, Field


class MinecraftLinkRequest(BaseModel):
    ign: str = Field(min_length=3, max_length=16)
    account_type: str = Field(pattern="^(premium|cracked)$")


class MinecraftProfile(BaseModel):
    ign: str
    uuid: str | None = None
    account_type: str
    premium: bool
    head_url: str
    avatar_url: str


class CartAddRequest(BaseModel):
    product_id: str = Field(min_length=1, max_length=80)
    quantity: int = Field(default=1, ge=1, le=99)


class CartUpdateRequest(BaseModel):
    product_id: str = Field(min_length=1, max_length=80)
    quantity: int = Field(default=1, ge=0, le=99)


class CheckoutRequest(BaseModel):
    coupon_code: str | None = Field(default=None, max_length=80)


class CouponValidateRequest(BaseModel):
    code: str = Field(min_length=1, max_length=80)


class CouponCreateRequest(BaseModel):
    code: str = Field(min_length=2, max_length=80)
    label: str = Field(min_length=1, max_length=160)
    coupon_type: str = Field(pattern="^(percentage|fixed|free_product)$")
    value: int = Field(default=0, ge=0)
    enabled: bool = True
    minimum_purchase: int = Field(default=0, ge=0)
    max_uses: int | None = Field(default=None, ge=1)
    max_uses_per_user: int | None = Field(default=None, ge=1)
    applicable_products: list[str] = []
    applicable_categories: list[str] = []


class StatusUpdateRequest(BaseModel):
    status: str = Field(pattern="^(pending|awaiting_staff|paid|processing|completed|cancelled|refunded)$")
    note: str = Field(default="", max_length=500)


class BotOrderLookupRequest(BaseModel):
    order_id: str = Field(min_length=3, max_length=80)


class AdminInviteCreateRequest(BaseModel):
    expires_in_hours: int | None = Field(default=72, ge=1, le=720)


class AdminInviteRedeemRequest(BaseModel):
    code: str = Field(min_length=12, max_length=120)
