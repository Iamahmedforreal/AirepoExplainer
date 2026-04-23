import logging

from requests import session
import uuid
from sqlalchemy.exc import SQLAlchemyError 
from app.models.users import User
from sqlalchemy import Select, exists, select   
from fastapi import HTTPException 

logger = logging.getLogger(__name__)

async def create_new_user(user_id: str, db) -> User:
    logger.info("[create_new_user] Attempting to create user: clerk_id=%s", user_id)
    try:
        # check if user already exists
        logger.debug("[create_new_user] Checking if user already exists: clerk_id=%s", user_id)
        if await does_user_exist(user_id, db):
            logger.warning("[create_new_user] Duplicate user detected: clerk_id=%s", user_id)
            raise ValueError("User already exists")

        new_user = User(id=user_id)

        db.add(new_user)
        logger.debug("[create_new_user] Committing new user to database: clerk_id=%s", user_id)
        await db.commit()
        await db.refresh(new_user)  
        logger.info("[create_new_user] User created successfully: clerk_id=%s", user_id)

        return new_user

    except ValueError:
        raise  

    except SQLAlchemyError as e:
        logger.error(
            "[create_new_user] SQLAlchemyError for clerk_id=%s — rolling back. Error: %s",
            user_id, e, exc_info=True
        )
        await db.rollback()
        raise Exception(f"Database error while creating user: {str(e)}")

async def does_user_exist(user_id: str, db) -> bool:
    logger.debug("[does_user_exist] Querying existence of user: clerk_id=%s", user_id)
    result = await db.execute(
        select(exists().where(User.id == user_id))
    )
    exists_flag = result.scalar()  
    logger.debug("[does_user_exist] Result for clerk_id=%s: exists=%s", user_id, exists_flag)
    return exists_flag

    
    
    


