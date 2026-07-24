from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.dependencies import get_or_create_current_user
from backend.schemas import CartAddRequest, CartUpdateRequest
from backend.services import cart as cart_service


router = APIRouter()


def current_cart(request: Request, db: Session):
    user = get_or_create_current_user(request, db)
    return cart_service.get_or_create_cart(db, user)


@router.get("/api/cart")
async def api_cart(request: Request, db: Session = Depends(get_db)) -> JSONResponse:
    cart = current_cart(request, db)
    return JSONResponse(cart_service.serialize_cart(cart))


@router.post("/api/cart/add")
async def api_cart_add(payload: CartAddRequest, request: Request, db: Session = Depends(get_db)) -> JSONResponse:
    cart = current_cart(request, db)
    try:
        cart = cart_service.add_product(db, cart, payload.product_id, payload.quantity)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return JSONResponse(cart_service.serialize_cart(cart))


@router.put("/api/cart/update")
async def api_cart_update(payload: CartUpdateRequest, request: Request, db: Session = Depends(get_db)) -> JSONResponse:
    cart = current_cart(request, db)
    try:
        cart = cart_service.update_quantity(db, cart, payload.product_id, payload.quantity)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return JSONResponse(cart_service.serialize_cart(cart))


@router.delete("/api/cart/remove")
async def api_cart_remove(payload: CartUpdateRequest, request: Request, db: Session = Depends(get_db)) -> JSONResponse:
    cart = current_cart(request, db)
    cart = cart_service.remove_product(db, cart, payload.product_id)
    return JSONResponse(cart_service.serialize_cart(cart))


@router.delete("/api/cart/clear")
async def api_cart_clear(request: Request, db: Session = Depends(get_db)) -> JSONResponse:
    cart = current_cart(request, db)
    cart = cart_service.clear_cart(db, cart)
    return JSONResponse(cart_service.serialize_cart(cart))
