from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.dependencies import get_or_create_current_user
from backend.schemas import CouponValidateRequest
from backend.services import cart as cart_service
from backend.services.admin_codes import redeem_admin_code
from backend.services.coupons import validate_coupon


router = APIRouter()


@router.post("/api/coupons/validate")
async def api_validate_coupon(payload: CouponValidateRequest, request: Request, db: Session = Depends(get_db)) -> JSONResponse:
    user = get_or_create_current_user(request, db)
    cart = cart_service.get_or_create_cart(db, user)
    subtotal = cart_service.serialize_cart(cart)["subtotal"]
    try:
        coupon, discount = validate_coupon(db, user, cart, payload.code, subtotal)
    except ValueError as exc:
        try:
            message = redeem_admin_code(db, user, payload.code)
        except ValueError:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return JSONResponse({"valid": True, "adminRedeemed": True, "message": message})
    cart.coupon_code = coupon.code
    db.commit()
    return JSONResponse({"valid": True, "code": coupon.code, "discount": discount, "finalTotal": subtotal - discount})
