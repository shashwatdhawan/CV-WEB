from datetime import datetime, timezone

from sqlalchemy.orm import Session

from backend.models import Cart, Coupon, CouponRedemption, User


def normalize_code(code: str) -> str:
    return code.strip().upper()


def serialize_coupon(coupon: Coupon) -> dict:
    return {
        "id": coupon.id,
        "code": coupon.code,
        "label": coupon.label,
        "type": coupon.coupon_type,
        "value": coupon.value,
        "enabled": coupon.enabled,
        "uses": coupon.uses,
        "maxUses": coupon.max_uses,
        "maxUsesPerUser": coupon.max_uses_per_user,
        "minimumPurchase": coupon.minimum_purchase,
        "applicableProducts": coupon.applicable_products.splitlines() if coupon.applicable_products else [],
        "applicableCategories": coupon.applicable_categories.splitlines() if coupon.applicable_categories else [],
    }


def validate_coupon(db: Session, user: User, cart: Cart, code: str, subtotal: int) -> tuple[Coupon, int]:
    coupon = db.query(Coupon).filter(Coupon.code == normalize_code(code)).first()
    if coupon is None or not coupon.enabled:
        raise ValueError("Invalid coupon code.")
    now = datetime.now(timezone.utc)
    if coupon.expires_at and coupon.expires_at < now:
        raise ValueError("This coupon has expired.")
    if coupon.max_uses is not None and coupon.uses >= coupon.max_uses:
        raise ValueError("This coupon has reached its usage limit.")
    if subtotal < coupon.minimum_purchase:
        raise ValueError("Cart total is below this coupon's minimum purchase.")

    user_uses = db.query(CouponRedemption).filter(CouponRedemption.coupon_id == coupon.id, CouponRedemption.user_id == user.id).count()
    if coupon.max_uses_per_user is not None and user_uses >= coupon.max_uses_per_user:
        raise ValueError("You have already used this coupon.")

    product_filters = set(coupon.applicable_products.splitlines()) if coupon.applicable_products else set()
    category_filters = set(coupon.applicable_categories.splitlines()) if coupon.applicable_categories else set()
    eligible_subtotal = 0
    for item in cart.items:
        if not item.product:
            continue
        product_ok = not product_filters or item.product_id in product_filters
        category_ok = not category_filters or item.product.category.slug in category_filters
        if product_ok and category_ok:
            eligible_subtotal += (item.product.sale_price if item.product.sale_price is not None else item.product.price) * item.quantity

    if eligible_subtotal <= 0:
        raise ValueError("This coupon does not apply to the items in your cart.")

    if coupon.coupon_type == "percentage":
        discount = eligible_subtotal * coupon.value // 100
    elif coupon.coupon_type == "fixed":
        discount = min(eligible_subtotal, coupon.value)
    elif coupon.coupon_type == "free_product":
        discount = min(eligible_subtotal, coupon.value)
    else:
        discount = 0

    return coupon, min(discount, subtotal)
