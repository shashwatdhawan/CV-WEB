from datetime import datetime, timezone

from sqlalchemy.orm import Session

from backend.models import Cart, CartItem, Product, User
from backend.services.catalog import serialize_product


def get_or_create_cart(db: Session, user: User) -> Cart:
    cart = db.query(Cart).filter(Cart.user_id == user.id).first()
    if cart is None:
        cart = Cart(user_id=user.id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart


def serialize_cart(cart: Cart) -> dict:
    items = []
    subtotal = 0
    for item in cart.items:
        if not item.product or not item.product.enabled:
            continue
        product_data = serialize_product(item.product)
        price = int(product_data["priceInr"])
        line_total = price * item.quantity
        subtotal += line_total
        items.append(
            {
                "id": item.id,
                "productId": item.product_id,
                "quantity": item.quantity,
                "product": product_data,
                "lineTotal": line_total,
            }
        )

    discount = 0
    return {
        "items": items,
        "subtotal": subtotal,
        "discount": discount,
        "finalTotal": subtotal - discount,
        "couponCode": cart.coupon_code,
        "totalItems": sum(item["quantity"] for item in items),
    }


def add_product(db: Session, cart: Cart, product_id: str, quantity: int) -> Cart:
    product = db.query(Product).filter(Product.id == product_id, Product.enabled.is_(True)).first()
    if product is None:
        raise ValueError("Product not found.")
    qty = max(1, min(int(quantity), 99))
    item = db.query(CartItem).filter(CartItem.cart_id == cart.id, CartItem.product_id == product_id).first()
    now = datetime.now(timezone.utc)
    if item is None:
        db.add(CartItem(cart_id=cart.id, product_id=product_id, quantity=qty))
    else:
        item.quantity = min(item.quantity + qty, 99)
        item.updated_at = now
    cart.updated_at = now
    db.commit()
    db.refresh(cart)
    return cart


def update_quantity(db: Session, cart: Cart, product_id: str, quantity: int) -> Cart:
    item = db.query(CartItem).filter(CartItem.cart_id == cart.id, CartItem.product_id == product_id).first()
    if item is None:
        raise ValueError("Cart item not found.")
    qty = int(quantity)
    if qty <= 0:
        db.delete(item)
    else:
        item.quantity = min(qty, 99)
        item.updated_at = datetime.now(timezone.utc)
    cart.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(cart)
    return cart


def remove_product(db: Session, cart: Cart, product_id: str) -> Cart:
    item = db.query(CartItem).filter(CartItem.cart_id == cart.id, CartItem.product_id == product_id).first()
    if item is not None:
        db.delete(item)
        cart.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(cart)
    return cart


def clear_cart(db: Session, cart: Cart) -> Cart:
    for item in list(cart.items):
        db.delete(item)
    cart.coupon_code = None
    cart.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(cart)
    return cart
