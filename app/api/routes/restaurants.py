from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
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
    return RestaurantResponse.model_validate(restaurant)


@router.get("", response_model=list[RestaurantResponse])
def list_restaurants(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[RestaurantResponse]:
    restaurants = restaurant_service.list_restaurants(db, current_user.id)
    return [RestaurantResponse.model_validate(r) for r in restaurants]


@router.get("/{restaurant_id}", response_model=RestaurantResponse)
def get_restaurant(
    restaurant_id: UUID,
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
    return RestaurantResponse.model_validate(restaurant)


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
