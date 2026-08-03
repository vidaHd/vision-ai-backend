from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.restaurant import Restaurant
from app.schemas.restaurant import RestaurantCreate, RestaurantUpdate


def count_menu_items(menu: dict[str, Any]) -> int:
    categories = menu.get("categories") or []
    total = 0
    for category in categories:
        if not isinstance(category, dict):
            continue
        items = category.get("items") or []
        if isinstance(items, list):
            total += len(items)
    return total


def list_restaurants(db: Session, user_id: UUID) -> list[Restaurant]:
    stmt = (
        select(Restaurant)
        .where(Restaurant.user_id == user_id)
        .order_by(Restaurant.created_at.desc())
    )
    return list(db.scalars(stmt).all())


def get_restaurant(
    db: Session,
    restaurant_id: UUID,
    user_id: UUID,
) -> Restaurant | None:
    restaurant = db.get(Restaurant, restaurant_id)
    if restaurant is None or restaurant.user_id != user_id:
        return None
    return restaurant


def create_restaurant(
    db: Session,
    payload: RestaurantCreate,
    user_id: UUID,
) -> Restaurant:
    """Insert a new restaurant row. Never updates or replaces an existing record."""
    restaurant = Restaurant(
        id=uuid4(),
        user_id=user_id,
        name=payload.name,
        address=payload.address,
        lat=payload.lat,
        lng=payload.lng,
        image_url=payload.image_url,
        menu=payload.menu,
        item_count=count_menu_items(payload.menu),
    )
    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)
    return restaurant


def update_restaurant(
    db: Session,
    restaurant: Restaurant,
    payload: RestaurantUpdate,
) -> Restaurant:
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(restaurant, field, value)
    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)
    return restaurant


def delete_restaurant(db: Session, restaurant: Restaurant) -> None:
    db.delete(restaurant)
    db.commit()
