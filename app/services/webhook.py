from requests import session
import uuid
from sqlalchemy.exc import SQLAlchemyError 
from app.models.users import User
from sqlalchemy import Select, exists, select   
from fastapi import HTTPException 

async def create_new_user(user_id: str, db) -> User:
    try:
        # check if user already exists
        if await does_user_exist(user_id, db):
            raise ValueError("User already exists")

        new_user = User(
            id=str(uuid.uuid4()),
            clerk_id=user_id,       
        )

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)  

        return new_user

    except ValueError:
        raise  

    except SQLAlchemyError as e:
        await db.rollback()
        raise Exception(f"Database error while creating user: {str(e)}")
    
async def does_user_exist(user_id: str, db) -> bool:
    result = await db.execute(
        select(exists().where(User.clerk_id == user_id))
    )
    return result.scalar()  

    
    
    


