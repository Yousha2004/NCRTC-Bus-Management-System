from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.core.security import SECRET_KEY, ALGORITHM
from pydantic import BaseModel

# Roles that can see data across all depots (everyone else is scoped to their depot)
GLOBAL_ROLES = {"admin", "control_operator"}


class TokenData(BaseModel):
    username: Optional[str] = None


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.username == token_data.username).first()
    if user is None:
        raise credentials_exception
    return user


def check_role(roles: list[str]):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role.name not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The user doesn't have enough privileges",
            )
        return current_user
    return role_checker


def sees_all_depots(user: User) -> bool:
    """admins and control-room operators see every depot; others are scoped."""
    return user.role.name in GLOBAL_ROLES


def scope_to_depot(query, model, user: User):
    """Restrict a query to the user's own depot unless they have a global role.

    `model` must have a `depot_id` column.
    """
    if sees_all_depots(user):
        return query
    return query.filter(model.depot_id == user.depot_id)
