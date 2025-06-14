from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from db import supabase

router = APIRouter()

class SettingsModel(BaseModel):
    user_id: str
    lot_size: float
    risk_percent: float
    symbols: list[str]
    strategy: str
    telegram_chat_id: str | None = None

@router.post("/save_settings")
async def save_settings(data: SettingsModel):
    try:
        supabase.save_settings(data.user_id, data.dict())
        return {"message": "Settings saved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/get_settings/{user_id}")
async def get_settings(user_id: str):
    return supabase.get_settings(user_id)

@router.get("/backtest/{user_id}/{symbol}/{strategy}")
async def backtest(user_id: str, symbol: str, strategy: str):
    # Dummy response for now
    return {"strategy": strategy, "symbol": symbol, "result": "Success (placeholder)"}
