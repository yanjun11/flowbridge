"""API 鉴权模块"""
import secrets

from fastapi import Header, HTTPException

from src.conf import settings


async def verify_api_key(x_api_key: str = Header(alias="X-API-Key")):
    """校验 API Key"""
    if x_api_key is None:
        raise HTTPException(status_code=401, detail="Missing X-API-Key header")
    if not secrets.compare_digest(x_api_key, settings.api_key):
        raise HTTPException(status_code=403, detail="Invalid API key")
