from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Category, Product
from backend.services.catalog import serialize_category, serialize_product


router = APIRouter()


@router.get("/api/categories")
async def api_categories(db: Session = Depends(get_db)) -> JSONResponse:
    categories = (
        db.query(Category)
        .filter(Category.enabled.is_(True))
        .order_by(Category.display_order, Category.name)
        .all()
    )
    return JSONResponse([serialize_category(category) for category in categories])


@router.get("/api/products")
async def api_products(db: Session = Depends(get_db)) -> JSONResponse:
    products = (
        db.query(Product)
        .join(Category)
        .filter(Product.enabled.is_(True), Category.enabled.is_(True))
        .order_by(Product.display_order, Product.name)
        .all()
    )
    return JSONResponse([serialize_product(product) for product in products])


@router.get("/api/featured-products")
async def api_featured_products(db: Session = Depends(get_db)) -> JSONResponse:
    products = (
        db.query(Product)
        .join(Category)
        .filter(Product.enabled.is_(True), Product.featured.is_(True), Category.enabled.is_(True))
        .order_by(Product.display_order, Product.name)
        .all()
    )
    return JSONResponse([serialize_product(product) for product in products])


@router.get("/api/products/{product_id}")
async def api_product(product_id: str, db: Session = Depends(get_db)) -> JSONResponse:
    product = (
        db.query(Product)
        .join(Category)
        .filter(Product.id == product_id, Product.enabled.is_(True), Category.enabled.is_(True))
        .first()
    )
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found.")
    return JSONResponse(serialize_product(product))
