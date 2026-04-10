"""FlowBridge 主应用"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from tortoise.contrib.fastapi import RegisterTortoise

from src.api import execution, webhook, workflow
from src.conf import settings
from src.service.logging_config import setup_logging
from src.service.plugin_manager import PluginManager
from src.service.scheduler import CronScheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    setup_logging(settings.log_level)
    # 启动时初始化插件
    plugin_manager = PluginManager()
    plugin_manager.register_all()
    scheduler = CronScheduler()
    await scheduler.start()
    yield
    # 关闭时清理资源
    CronScheduler().shutdown()


app = FastAPI(
    title="FlowBridge",
    description="国内版 Zapier - 自动化工作流平台",
    version="0.1.0",
    lifespan=lifespan,
)

# 注册路由
app.include_router(webhook.router, prefix="/api")
app.include_router(workflow.router, prefix="/api")
app.include_router(execution.router, prefix="/api")

# 注册数据库
RegisterTortoise(
    app,
    config=settings.TORTOISE_ORM,
    generate_schemas=True,
    add_exception_handlers=True,
)


@app.get("/")
async def root():
    """健康检查"""
    return {"status": "ok", "service": "FlowBridge"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
