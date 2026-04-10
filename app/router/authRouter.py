from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.db import get_db
from app.schema.authSchema import UserRegister, RegisterResponse



router = APIRouter()

# User registration endpoint
@router.post("/register",  status_code=201) 
async def register(   user_data: UserRegister, db:  AsyncSession =  Depends(get_db)) -> RegisterResponse: 
    pass
