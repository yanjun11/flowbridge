"""通用 HTTP 请求动作"""

import logging
from typing import Any, Dict

import httpx

from src.plugins.action.wecom_notify import WecomNotifyAction
from src.plugins.base import ActionPlugin, ActionResult
from src.service.template import render_template

logger = logging.getLogger(__name__)


class HttpRequestAction(ActionPlugin):
    """发送 HTTP 请求到后端服务"""

    _ALLOWED_METHODS = {"GET", "POST", "PUT", "DELETE", "PATCH"}

    @property
    def action_type(self) -> str:
        return "http_request"

    async def validate_config(self, config: Dict[str, Any]) -> bool:
        """验证配置"""
        if "url" not in config:
            return False

        method = str(config.get("method", "POST")).strip().upper()
        return method in self._ALLOWED_METHODS

    async def execute(self, context: Dict[str, Any], config: Dict[str, Any]) -> ActionResult:
        """执行 HTTP 请求"""
        try:
            url = render_template(str(config["url"]), context)
            method = str(config.get("method", "POST")).strip().upper()
            timeout = float(config.get("timeout", 30))
            allow_internal = bool(config.get("allow_internal", False))

            if method not in self._ALLOWED_METHODS:
                return ActionResult(success=False, message=f"不支持的 HTTP 方法: {method}")

            if not allow_internal and not WecomNotifyAction._is_safe_webhook_url(url):
                return ActionResult(success=False, message="请求 URL 不安全，仅允许公网 HTTPS 地址")

            headers = self._render_dict_values(config.get("headers"), context)
            body = self._render_dict_values(config.get("body"), context)

            request_kwargs: Dict[str, Any] = {}
            if headers:
                request_kwargs["headers"] = headers
            if body:
                if method == "GET":
                    request_kwargs["params"] = body
                else:
                    request_kwargs["json"] = body

            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.request(method, url, **request_kwargs)

            response_body: Any
            try:
                response_body = resp.json()
            except Exception:
                response_body = resp.text

            success = 200 <= resp.status_code < 400
            message = "请求成功" if success else f"HTTP 错误: {resp.status_code}"
            return ActionResult(
                success=success,
                message=message,
                data={"status_code": resp.status_code, "response": response_body},
            )
        except Exception as e:
            logger.error("Failed to send http request: %s", e)
            return ActionResult(success=False, message=f"请求失败: {str(e)}")

    @classmethod
    def _render_dict_values(cls, data: Any, context: Dict[str, Any]) -> Any:
        if data is None:
            return None
        if isinstance(data, str):
            return render_template(data, context)
        if isinstance(data, dict):
            return {str(k): cls._render_dict_values(v, context) for k, v in data.items()}
        if isinstance(data, list):
            return [cls._render_dict_values(v, context) for v in data]
        return data
