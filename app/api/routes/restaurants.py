from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.restaurant import (
    RestaurantCreate,
    RestaurantResponse,
    RestaurantUpdate,
)
from app.services import restaurants as restaurant_service
from app.services.cache import (
    cache_get_json,
    cache_set_json,
    invalidate_user_restaurants,
    restaurant_item_key,
    restaurants_list_key,
)

router = APIRouter(prefix="/restaurants", tags=["restaurants"])


@router.post(
    "",
    response_model=RestaurantResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_restaurant(
    payload: RestaurantCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RestaurantResponse:
    restaurant = restaurant_service.create_restaurant(db, payload, current_user.id)
    invalidate_user_restaurants(current_user.id, restaurant.id)
    return RestaurantResponse.model_validate(restaurant)


@router.get("", response_model=list[RestaurantResponse])
def list_restaurants(
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[RestaurantResponse]:
    key = restaurants_list_key(current_user.id)
    cached = cache_get_json(key)
    if isinstance(cached, list):
        response.headers["X-Cache"] = "HIT"
        return [RestaurantResponse.model_validate(item) for item in cached]

    restaurants = restaurant_service.list_restaurants(db, current_user.id)
    payload = [
        RestaurantResponse.model_validate(r).model_dump(mode="json")
        for r in restaurants
    ]
    cache_set_json(key, payload)
    response.headers["X-Cache"] = "MISS"
    return [RestaurantResponse.model_validate(item) for item in payload]


@router.get("/{restaurant_id}", response_model=RestaurantResponse)
def get_restaurant(
    restaurant_id: UUID,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RestaurantResponse:
    key = restaurant_item_key(current_user.id, restaurant_id)
    cached = cache_get_json(key)
    if isinstance(cached, dict):
        response.headers["X-Cache"] = "HIT"
        return RestaurantResponse.model_validate(cached)

    restaurant = restaurant_service.get_restaurant(
        db, restaurant_id, current_user.id
    )
    if restaurant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found",
        )
    body = RestaurantResponse.model_validate(restaurant)
    cache_set_json(key, body.model_dump(mode="json"))
    response.headers["X-Cache"] = "MISS"
    return body


@router.patch("/{restaurant_id}", response_model=RestaurantResponse)
def update_restaurant(
    restaurant_id: UUID,
    payload: RestaurantUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RestaurantResponse:
    restaurant = restaurant_service.get_restaurant(
        db, restaurant_id, current_user.id
    )
    if restaurant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found",
        )
    updated = restaurant_service.update_restaurant(db, restaurant, payload)
    invalidate_user_restaurants(current_user.id, restaurant_id)
    return RestaurantResponse.model_validate(updated)


@router.delete("/{restaurant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_restaurant(
    restaurant_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    restaurant = restaurant_service.get_restaurant(
        db, restaurant_id, current_user.id
    )
    if restaurant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found",
        )
    restaurant_service.delete_restaurant(db, restaurant)
    invalidate_user_restaurants(current_user.id, restaurant_id)
