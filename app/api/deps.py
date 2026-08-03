from __future__ import annotations

from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User
from app.services import users as user_service

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise credentials_exception

    token = credentials.credentials
    try:
        payload = decode_access_token(token)
        subject = payload.get("sub")
        if not subject or not isinstance(subject, str):
            raise credentials_exception
        user_id = UUID(subject)
    except (jwt.PyJWTError, ValueError):
        raise credentials_exception from None

    user = user_service.get_user_by_id(db, user_id)
    if user is None:
        raise credentials_exception
    return user
