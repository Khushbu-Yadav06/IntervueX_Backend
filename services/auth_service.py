from sqlalchemy.orm import Session
from pwdlib import PasswordHash

from database.models import User


password_hash = PasswordHash.recommended()


def hash_password(password: str):
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str):
    return password_hash.verify(plain_password, hashed_password)


def register_user(db: Session, full_name: str, email: str, password: str):

    # Check whether the email is already registered
    existing_user = db.query(User).filter(
        User.email == email
    ).first()

    if existing_user:
        return None

    # Hash the password
    hashed_password = hash_password(password)

    # Create the user
    new_user = User(
        full_name=full_name,
        email=email,
        hashed_password=hashed_password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


def authenticate_user(db: Session, email: str, password: str):

    # Find user by email
    user = db.query(User).filter(
        User.email == email
    ).first()

    if not user:
        return None

    # Verify password
    if not verify_password(password, user.hashed_password):
        return None

    if not user.is_active:
        return None

    return user