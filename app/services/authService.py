from fastapi import HTTPException
from requests import Session
from sqlalchemy import select
from passlib.context import CryptContext
from app.models.users import User
from app.schema.authSchema import UserRegister
from sqlalchemy import exists

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto" , bcrypt__rounds=12)


async def create_user(db: Session, user_data: UserRegister) -> UserRegister:

  try:
    # Check if user already exists by email
    stmt = select(User).where(User.email == user_data.email)
    result = await db.execute(stmt)
    existing_user = result.scalars().first()

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    if user_data.password != user_data.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    # Hash password
    hashed_password = pwd_context.hash(user_data.password)
    
    # Create new user
    new_user = User(
        username=user_data.username,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        email=user_data.email,
        hashed_password=hashed_password
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return UserRegister(
        success=True,
        message="User registered successfully"
    )
  except HTTPException as error:
     raise HTTPException(status_code=error.status_code, detail=error.detail)
    
