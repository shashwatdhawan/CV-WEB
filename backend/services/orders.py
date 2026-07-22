import secrets
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from backend.models import Cart, Coupon, CouponRedemption, Order, OrderItem, OrderStatusHistory, User
from backend.services.cart import clear_cart
from backend.services.coupons import validate_coupon


VALID_STATUSES = {"pending", "awaiting_staff", "paid", "processing", "completed", "cancelled", "refunded"}


def generate_order_number(db: Session) -> str:
    while True:
        number = f"CV-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{secrets.token_hex(3).upper()}"
        if not db.query(Order).filter(Order.order_number == number).first():
            return number


def serialize_order(order: Order) -> dict:
    return {
        "id": order.id,
        "orderId": order.order_number,
        "discordId": order.discord_id,
        "discordUsername": order.discord_username,
        "minecraftIgn": order.minecraft_ign,
        "minecraftAccountType": order.minecraft_account_type,
        "minecraftPremium": order.minecraft_premium,
        "status": order.status,
        "subtotal": order.subtotal,
        "discount": order.discount,
        "coupon": order.coupon_code,
        "finalTotal": order.final_total,
        "createdAt": order.created_at.isoformat() if order.created_at else None,
        "updatedAt": order.updated_at.isoformat() if order.updated_at else None,
        "items": [
            {
                "productId": item.product_id,
                "name": item.product_name,
                "category": item.category_slug,
                "quantity": item.quantity,
                "unitPrice": item.unit_price,
                "lineTotal": item.line_total,
            }
            for item in order.items
        ],
        "history": [
            {
                "oldStatus": entry.old_status,
                "newStatus": entry.new_status,
                "note": entry.note,
                "createdAt": entry.created_at.isoformat() if entry.created_at else None,
            }
            for entry in order.history
        ],
    }


def create_order_from_cart(db: Session, user: User, cart: Cart, coupon_code: str | None = None) -> Order:
    valid_items = [item for item in cart.items if item.product and item.product.enabled]
    if not valid_items:
        raise ValueError("Your cart is empty.")

    subtotal = 0
    for item in valid_items:
        price = item.product.sale_price if item.product.sale_price is not None else item.product.price
        subtotal += price * item.quantity

    discount = 0
    coupon: Coupon | None = None
    effective_coupon_code = coupon_code or cart.coupon_code
    if effective_coupon_code:
        coupon, discount = validate_coupon(db, user, cart, effective_coupon_code, subtotal)

    order = Order(
        order_number=generate_order_number(db),
        user_id=user.id,
        discord_id=user.discord_id,
        discord_username=user.discord_username,
        minecraft_ign=user.minecraft_ign,
        minecraft_uuid=user.minecraft_uuid,
        minecraft_account_type=user.minecraft_account_type,
        minecraft_premium=bool(user.minecraft_premium),
        status="pending",
        subtotal=subtotal,
        discount=discount,
        coupon_code=coupon.code if coupon else None,
        final_total=subtotal - discount,
    )
    db.add(order)
    db.flush()

    for item in valid_items:
        price = item.product.sale_price if item.product.sale_price is not None else item.product.price
        db.add(
            OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                product_name=item.product.name,
                category_slug=item.product.category.slug,
                quantity=item.quantity,
                unit_price=price,
                line_total=price * item.quantity,
            )
        )

    db.add(OrderStatusHistory(order_id=order.id, old_status=None, new_status="pending", note="Order created from checkout."))
    if coupon:
        coupon.uses += 1
        db.add(CouponRedemption(coupon_id=coupon.id, user_id=user.id, order_id=order.id, discount=discount))

    user.order_count += 1
    user.purchase_count += sum(item.quantity for item in valid_items)
    user.money_spent_inr += order.final_total
    clear_cart(db, cart)
    db.commit()
    db.refresh(order)
    return order


def update_order_status(db: Session, order: Order, new_status: str, actor: User | None, note: str = "") -> Order:
    if new_status not in VALID_STATUSES:
        raise ValueError("Invalid order status.")
    old_status = order.status
    order.status = new_status
    order.updated_at = datetime.now(timezone.utc)
    db.add(OrderStatusHistory(order_id=order.id, old_status=old_status, new_status=new_status, changed_by_user_id=actor.id if actor else None, note=note))
    db.commit()
    db.refresh(order)
    return order
