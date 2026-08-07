from datetime import datetime, timezone

from sqlalchemy.orm import Session

from backend.models import Category, Product


DEFAULT_CATEGORIES = [
    {"slug": "ranks", "name": "Ranks", "display_order": 1},
    {"slug": "coins", "name": "Coins", "display_order": 2},
    {"slug": "keys", "name": "Keys", "display_order": 3},
]


def product(id: str, category: str, name: str, description: str, price: int, price_usd: str, theme: str, image: str, display_order: int, features: list[str], featured: bool = False) -> dict:
    return {
        "id": id,
        "category": category,
        "name": name,
        "description": description,
        "price": price,
        "price_usd": price_usd,
        "theme": theme,
        "image": image,
        "featured": featured,
        "display_order": display_order,
        "features": features,
    }


DEFAULT_PRODUCTS = [
    product("warrior", "ranks", "Warrior", "Starter Cloudverse rank with useful Lifesteal perks", 50, "0.60", "warrior", "/static/assets/products/warrior.png", 1, [
        "Access to 2 homes",
        "Access to 15 coin flips",
        "Access to 2 vaults",
        "Priority queue in hub",
        "Special role on Discord",
        "Access to Warrior kit",
        "Priority support in Discord",
        "RTP cooldown decreased by 60 seconds",
    ], True),
    product("champion", "ranks", "Aurora", "Aurora rank with stronger daily rewards and commands", 100, "1.20", "champion", "/static/assets/products/champion.png", 2, [
        "Access to 25 coin flips",
        "Access to 3 homes",
        "Access to /sit command",
        "Access to /ec command",
        "Aurora kit",
        "Priority queue in hub",
        "Access to 2 vaults",
        "RTP cooldown decreased by 90 seconds",
        "Priority support in Discord",
        "Special role on Discord",
        "100 shards every day",
        "200k every day",
    ], True),
    product("radiant", "ranks", "Radiant", "Radiant rank for active players who want premium perks", 250, "3.00", "radiant", "/static/assets/products/radiant.png", 3, [
        "Access to 50 coin flips",
        "Access to 4 homes",
        "Access to 3 vaults",
        "Access to /sit command",
        "Access to /ec command",
        "Access to /workbench command",
        "Radiant kit",
        "Priority queue",
        "RTP cooldown decreased by 120 seconds",
        "Priority role",
        "Priority support",
        "150 shards every day",
        "300k every day",
    ], True),
    product("daddy", "ranks", "DADDY", "High tier rank with powerful commands and rewards", 500, "6.00", "daddy", "/static/assets/products/daddy.png", 4, [
        "Access to 75 coin flips",
        "Access to 4 homes",
        "Access to /sit command",
        "Access to /lay command",
        "Access to /ec command",
        "Access to /anvil command",
        "Access to /workbench command",
        "DADDY kit",
        "Priority queue in hub",
        "Access to 4 vaults",
        "RTP cooldown decreased by 180 seconds",
        "Priority support in Discord",
        "Special role on Discord",
        "300 shards every day",
        "500k every day",
    ]),
    product("custom", "ranks", "CUSTOM", "Custom rank with your chosen name and premium commands", 750, "9.00", "custom", "/static/assets/products/custom.png", 5, [
        "Access to 100 coin flips",
        "Access to 5 homes",
        "Access to /sit command",
        "Access to /lay command",
        "Access to /spin command",
        "Access to /ec command",
        "Access to /anvil command",
        "Access to /workbench command",
        "Access to /loom command",
        "Access to /grindstone command",
        "Custom kit and rank name of your choice",
        "Priority queue in hub",
        "Access to 4 vaults",
        "RTP cooldown decreased by 360 seconds",
        "Priority support in Discord",
        "Special role on Discord",
        "500 shards every day",
        "1m every day",
    ]),
    product("coins-1000", "coins", "1,000 Coins", "Starter CV coin pack", 150, "1.80", "coins", "/static/assets/products/coins-1000.png", 6, ["1,000 in-game coins", "Price: Rs. 150", "Digital delivery after purchase"], True),
    product("coins-2500", "coins", "2,500 Coins", "Popular CV coin pack", 300, "3.60", "coins", "/static/assets/products/coins-2500.png", 7, ["2,500 in-game coins", "Price: Rs. 300", "Digital delivery after purchase"], True),
    product("coins-5000", "coins", "5,000 Coins", "Balanced CV coin pack", 450, "5.40", "coins", "/static/assets/products/coins-5000.png", 8, ["5,000 in-game coins", "Price: Rs. 450", "Digital delivery after purchase"]),
    product("coins-8000", "coins", "8,000 Coins", "Great value CV coin pack", 750, "9.00", "coins", "/static/assets/products/coins-8000.png", 9, ["8,000 in-game coins", "Price: Rs. 750", "Digital delivery after purchase"], True),
    product("coins-15000", "coins", "15,000 Coins", "Large CV coin bundle", 1250, "15.00", "coins", "/static/assets/products/coins-15000.png", 10, ["15,000 in-game coins", "Price: Rs. 1,250", "Digital delivery after purchase"]),
    product("coins-25000", "coins", "25,000 Coins", "Biggest CV coin pack", 2000, "24.00", "coins", "/static/assets/products/coins-25000.png", 11, ["25,000 in-game coins", "Price: Rs. 2,000", "Digital delivery after purchase"], True),
    product("cloud-key", "keys", "Cloud Key", "Premium Cloudverse crate key", 250, "3.00", "cloud-key", "/static/assets/products/cloud-key.png", 12, ["1x Cloud Key", "Price: Rs. 250", "Digital delivery after purchase"], True),
    product("matrix-key", "keys", "Matrix Key", "Rare key for stronger Lifesteal rewards", 150, "1.80", "matrix-key", "/static/assets/products/matrix-key.png", 13, ["1x Matrix Key", "Price: Rs. 150", "Digital delivery after purchase"]),
    product("amethyst-key", "keys", "Amethyst Crate Key", "Amethyst crate key for useful rewards", 75, "0.90", "amethyst-key", "/static/assets/products/amethyst-key.png", 14, ["1x Amethyst Crate Key", "Price: Rs. 75", "Digital delivery after purchase"]),
    product("special-edition-key", "keys", "Special Edition Key", "Limited crate key with premium rewards", 300, "3.60", "special-edition-key", "/static/assets/products/special-edition-key.png", 15, ["1x Special Edition Key", "Price: Rs. 300", "Limited premium key"]),
]


def serialize_product(product: Product) -> dict:
    price = product.sale_price if product.sale_price is not None else product.price
    return {
        "id": product.id,
        "category": product.category.slug,
        "name": product.name,
        "description": product.description,
        "subtitle": product.description,
        "price": product.price,
        "salePrice": product.sale_price,
        "priceInr": price,
        "priceUsd": product.price_usd,
        "image": product.image,
        "featured": product.featured,
        "enabled": product.enabled,
        "displayOrder": product.display_order,
        "theme": product.theme,
        "artType": product.art_type,
        "features": product.features.splitlines() if product.features else [],
        "createdAt": product.created_at.isoformat() if product.created_at else None,
        "updatedAt": product.updated_at.isoformat() if product.updated_at else None,
    }


def serialize_category(category: Category) -> dict:
    return {
        "id": category.id,
        "slug": category.slug,
        "name": category.name,
        "displayOrder": category.display_order,
        "enabled": category.enabled,
    }


def seed_catalog(db: Session) -> None:
    now = datetime.now(timezone.utc)
    categories: dict[str, Category] = {}
    for item in DEFAULT_CATEGORIES:
        category = db.query(Category).filter(Category.slug == item["slug"]).first()
        if category is None:
            category = Category(**item)
            db.add(category)
            db.flush()
        else:
            category.name = item["name"]
            category.display_order = item["display_order"]
            category.enabled = True
            category.updated_at = now
        categories[category.slug] = category

    current_ids = {item["id"] for item in DEFAULT_PRODUCTS}
    db.query(Product).filter(~Product.id.in_(current_ids)).update({"enabled": False, "updated_at": now}, synchronize_session=False)

    for item in DEFAULT_PRODUCTS:
        product = db.query(Product).filter(Product.id == item["id"]).first()
        category = categories[item["category"]]
        values = {
            "name": item["name"],
            "description": item["description"],
            "category_id": category.id,
            "price": item["price"],
            "sale_price": item.get("sale_price"),
            "price_usd": item["price_usd"],
            "image": item["image"],
            "theme": item["theme"],
            "art_type": "image",
            "features": "\n".join(item["features"]),
            "featured": bool(item.get("featured", False)),
            "enabled": True,
            "display_order": item["display_order"],
            "updated_at": now,
        }
        if product is None:
            db.add(Product(id=item["id"], **values))
        else:
            for key, value in values.items():
                setattr(product, key, value)
    db.commit()
