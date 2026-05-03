"""Java 后端工具接口客户端。"""

import uuid
from typing import Any

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from aptguide.core.config import Settings
from aptguide.core.logging import get_logger

logger = get_logger(__name__)


class LeaseToolError(Exception):
    """工具接口业务错误。"""

    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(f"LeaseToolError({code}): {message}")


class LeaseToolClient:
    """lease 后端工具接口客户端。"""

    def __init__(self, settings: Settings):
        self.base_url = settings.lease_base_url.rstrip("/")
        self.token = settings.lease_internal_token
        self.timeout = settings.lease_request_timeout_seconds
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """获取或创建 HTTP 客户端。"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                headers={
                    "X-Internal-Token": self.token,
                    "Content-Type": "application/json",
                },
            )
        return self._client

    async def close(self) -> None:
        """关闭客户端。"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    def _make_request_id(self) -> str:
        """生成请求 ID。"""
        return f"aptguide-{uuid.uuid4().hex[:12]}"

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=(
            retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError))
        ),
    )
    async def _request(
        self,
        method: str,
        path: str,
        *,
        user_id: str | None = None,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """发送请求并处理响应。"""
        client = await self._get_client()
        headers = {"X-Request-Id": self._make_request_id()}
        if user_id:
            headers["X-User-Id"] = user_id

        try:
            response = await client.request(
                method, path, json=json, params=params, headers=headers
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.error(
                "HTTP error",
                status=e.response.status_code,
                path=path,
                response=e.response.text,
            )
            raise
        except (httpx.TimeoutException, httpx.NetworkError) as e:
            logger.error("Network error", path=path, error=str(e))
            raise

        data = response.json()
        if data.get("code") != 0:
            raise LeaseToolError(data["code"], data.get("message", "Unknown error"))

        return data.get("data", {})

    # ========== 健康检查 ==========

    async def health_check(self) -> bool:
        """检查 lease 后端是否可达。"""
        try:
            data = await self._request("GET", "/internal/ai/tools/health")
            return data == "ok"
        except Exception as e:
            logger.warning("Health check failed", error=str(e))
            return False

    # ========== 房源接口 ==========

    async def search_rooms(
        self,
        *,
        city_id: int | None = None,
        district_id: int | None = None,
        max_rent: int | None = None,
        min_rent: int | None = None,
        payment_type: str | None = None,
        lease_term_months: int | None = None,
        tags: list[str] | None = None,
        room_ids: list[int] | None = None,
        limit: int = 5,
    ) -> dict[str, Any]:
        """精确条件搜索房源。"""
        payload = {}
        if city_id is not None:
            payload["city_id"] = city_id
        if district_id is not None:
            payload["district_id"] = district_id
        if max_rent is not None:
            payload["max_rent"] = max_rent
        if min_rent is not None:
            payload["min_rent"] = min_rent
        if payment_type:
            payload["payment_type"] = payment_type
        if lease_term_months is not None:
            payload["lease_term_months"] = lease_term_months
        if tags:
            payload["tags"] = tags
        if room_ids:
            payload["room_ids"] = room_ids
        payload["limit"] = limit

        return await self._request("POST", "/internal/ai/tools/room/search", json=payload)

    # ========== 预约接口 ==========

    async def create_appointment(
        self,
        user_id: str,
        *,
        apartment_id: int,
        room_id: int,
        appointment_time: str,
        remark: str | None = None,
    ) -> dict[str, Any]:
        """创建看房预约。"""
        payload = {
            "apartment_id": apartment_id,
            "room_id": room_id,
            "appointment_time": appointment_time,
        }
        if remark:
            payload["remark"] = remark

        return await self._request(
            "POST",
            "/internal/ai/tools/appointment/create",
            user_id=user_id,
            json=payload,
        )

    async def list_my_appointments(self, user_id: str) -> dict[str, Any]:
        """查询当前用户的预约列表。"""
        return await self._request(
            "GET",
            "/internal/ai/tools/appointment/list-mine",
            user_id=user_id,
        )

    # ========== 租约接口 ==========

    async def list_my_leases(self, user_id: str) -> dict[str, Any]:
        """查询当前用户的租约列表。"""
        return await self._request(
            "GET",
            "/internal/ai/tools/lease/list-mine",
            user_id=user_id,
        )
