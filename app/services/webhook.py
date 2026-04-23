import logging

from requests import session
import uuid
from sqlalchemy.exc import SQLAlchemyError 
from app.models.users import User
from sqlalchemy import  exists, select   
from sqlalchemy import IntegrityError 

logger = logging.getLogger(__name__)

async def create_new_user(user_id: str, db) -> User:
    
    try:
        # check if user already exists

        if await does_user_exist(user_id, db):
            raise ValueError("User already exists")

        new_user = User(id=user_id)
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)  
        return new_user

    except IntegrityError:
        await db.rollback()
        logger.warning("user already exist: %s" , user_id)
        return None
      

async def does_user_exist(user_id: str, db) -> bool:
    logger.debug("[does_user_exist] Querying existence of user: clerk_id=%s", user_id)
    result = await db.execute(
        select(exists().where(User.id == user_id))
    )
    exists_flag = result.scalar()  
    logger.debug("[does_user_exist] Result for clerk_id=%s: exists=%s", user_id, exists_flag)
    return exists_flag

    
    
    


