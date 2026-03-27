"""配置管理模块"""
import os
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""

    # 服务配置
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # 数据库
    database_url: str = "postgresql://flowbridge:flowbridge@localhost:5432/flowbridge"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # 飞书配置
    feishu_app_id: str = ""
    feishu_app_secret: str = ""
    feishu_webhook_secret: str = ""

    # 企微配置
    wecom_webhook_url: str = ""

    # 日志
    log_level: str = "INFO"

    # CORS
    cors_origins: List[str] = ["*"]

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()


# Tortoise ORM 配置
TORTOISE_ORM = {
    "connections": {"default": settings.database_url},
    "apps": {
        "models": {
            "models": ["src.dao.orm.model", "aerich.models"],
            "default_connection": "default",
        }
    },
}
