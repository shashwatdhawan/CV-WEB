from datetime import datetime, timezone

from sqlalchemy.orm import Session

from backend.models import Category, Product


DEFAULT_CATEGORIES = [
    {"slug": "ranks", "name": "Ranks", "display_order": 1},
    {"slug": "coins", "name": "Coins", "display_order": 2},
    {"slug": "keys", "name": "Keys", "display_order": 3},
]

DEFAULT_PRODUCTS = [
    {
        "id": "warrior",
        "category": "ranks",
        "name": "Warrior",
        "description": "Starter rank for Lifesteal warriors",
        "price": 50,
        "price_usd": "0.52",
        "theme": "warrior",
        "image": "/static/assets/products/warrior.png",
        "featured": True,
        "display_order": 1,
        "features": ["Warrior rank tag", "1x Warrior crate key", "Rs. 10,000 in-game money", "Basic /kit warrior", "Discord buyer role"],
    },
    {
        "id": "champion",
        "category": "ranks",
        "name": "Champion",
        "description": "Balanced rank with stronger starter perks",
        "price": 100,
        "price_usd": "1.05",
        "theme": "champion",
        "image": "/static/assets/products/champion.png",
        "featured": True,
        "display_order": 2,
        "features": ["Champion rank tag", "2x Champion crate keys", "Rs. 25,000 in-game money", "Champion kit", "Priority queue style tag"],
    },
    {
        "id": "radiant",
        "category": "ranks",
        "name": "Radiant",
        "description": "Premium glowing rank for daily players",
        "price": 250,
        "price_usd": "2.62",
        "theme": "radiant",
        "image": "/static/assets/products/radiant.png",
        "featured": True,
        "display_order": 3,
        "features": ["Radiant rank tag", "4x Radiant crate keys", "Rs. 75,000 in-game money", "Radiant particles", "Premium kit cooldown"],
    },
    {
        "id": "daddy",
        "category": "ranks",
        "name": "DADDY",
        "description": "High tier rank with bold rewards",
        "price": 500,
        "price_usd": "5.24",
        "theme": "daddy",
        "image": "/static/assets/products/daddy.png",
        "display_order": 4,
        "features": ["DADDY rank tag", "8x DADDY crate keys", "Rs. 175,000 in-game money", "Special /kit daddy", "Exclusive Discord role"],
    },
    {
        "id": "custom",
        "category": "ranks",
        "name": "CUSTOM",
        "description": "Custom rank made with your selected style",
        "price": 750,
        "price_usd": "7.87",
        "theme": "custom",
        "image": "/static/assets/products/custom.png",
        "display_order": 5,
        "features": ["Custom rank display name", "Custom rank color discussion", "12x premium crate keys", "Rs. 300,000 in-game money", "Custom setup support"],
    },
    {
        "id": "coins-200",
        "category": "coins",
        "name": "200 Coins",
        "description": "Small coin pack for Cloudverse Lifesteal",
        "price": 30,
        "price_usd": "0.36",
        "theme": "coins",
        "image": "/static/assets/products/coins.png",
        "display_order": 6,
        "features": ["200 in-game coins", "Price: Rs. 30", "Digital delivery after purchase"],
    },
    {
        "id": "coins-1000",
        "category": "coins",
        "name": "1,000 Coins",
        "description": "Best starter coin bundle",
        "price": 100,
        "price_usd": "1.20",
        "theme": "coins",
        "image": "/static/assets/products/coins.png",
        "featured": True,
        "display_order": 7,
        "features": ["1,000 in-game coins", "Price: Rs. 100", "Digital delivery after purchase"],
    },
    {
        "id": "coins-2000",
        "category": "coins",
        "name": "2,000 Coins",
        "description": "Bigger coin bundle for upgrades",
        "price": 150,
        "price_usd": "1.80",
        "theme": "coins",
        "image": "/static/assets/products/coins.png",
        "display_order": 8,
        "features": ["2,000 in-game coins", "Price: Rs. 150", "Digital delivery after purchase"],
    },
    {
        "id": "cloud-key",
        "category": "keys",
        "name": "Cloud Key",
        "description": "Premium Cloudverse crate key",
        "price": 250,
        "price_usd": "3.00",
        "theme": "cloud-key",
        "image": "/static/assets/products/cloud-key.png",
        "featured": True,
        "display_order": 9,
        "features": ["1x Cloud Key", "Price: Rs. 250", "Digital delivery after purchase"],
    },
    {
        "id": "matrix-key",
        "category": "keys",
        "name": "Matrix Key",
        "description": "Rare key for stronger Lifesteal rewards",
        "price": 150,
        "price_usd": "1.80",
        "theme": "matrix-key",
        "image": "/static/assets/products/matrix-key.png",
        "display_order": 10,
        "features": ["1x Matrix Key", "Price: Rs. 150", "Digital delivery after purchase"],
    },
    {
        "id": "amethyst-key",
        "category": "keys",
        "name": "Amethyst Key",
        "description": "Amethyst crate key for useful rewards",
        "price": 75,
        "price_usd": "0.90",
        "theme": "amethyst-key",
        "image": "/static/assets/products/amethyst-key.png",
        "display_order": 11,
        "features": ["1x Amethyst Key", "Price: Rs. 75", "Digital delivery after purchase"],
    },
    {
        "id": "special-edition-key",
        "category": "keys",
        "name": "Special Edition Key",
        "description": "Limited crate key with premium rewards",
        "price": 300,
        "price_usd": "3.60",
        "theme": "special-edition-key",
        "image": "/static/assets/products/special-edition-key.png",
        "display_order": 12,
        "features": ["1x Special Edition Key", "Price: Rs. 300", "Limited premium key"],
    },
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
            category.updated_at = now
        categories[category.slug] = category

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
