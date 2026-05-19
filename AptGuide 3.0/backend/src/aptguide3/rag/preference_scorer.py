from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, Field, ValidationError

from aptguide3.rag.schemas import PreferenceScore, ValidatedRoom


class PreferenceScoreBatch(BaseModel):
    scores: list[PreferenceScore] = Field(default_factory=list)


class LLMPreferenceScorer:
    def __init__(self, client: Any | None, model: str) -> None:
        self.client = client
        self.model = model

    def score(
        self,
        raw_message: str,
        soft_preferences: list[str],
        rooms: list[ValidatedRoom],
    ) -> dict[int, PreferenceScore]:
        if self.client is None or not soft_preferences or not rooms:
            return {
                room.room_id: PreferenceScore(room_id=room.room_id, score=0.5, reason="无偏好评分，使用中性分。")
                for room in rooms
            }
        payload = {
            "user_message": raw_message,
            "soft_preferences": soft_preferences,
            "rooms": [
                {
                    "room_id": room.room_id,
                    "rent": room.rent,
                    "district_name": room.district_name,
                    "tags": room.tags,
                    "facilities": room.facilities,
                    "payment_types": room.payment_types,
                    "lease_terms": room.lease_terms,
                }
                for room in rooms
            ],
        }
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "你是租房推荐偏好匹配评分器。只根据输入的房源公开字段评分，"
                            "不要编造价格、地址、上架状态或可预约状态。返回 JSON: "
                            '{"scores":[{"room_id":1,"score":0.0,"matched_preferences":[],'
                            '"missing_preferences":[],"reason":""}]}'
                        ),
                    },
                    {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
                ],
                response_format={"type": "json_object"},
                temperature=0,
            )
            content = response.choices[0].message.content or "{}"
            batch = PreferenceScoreBatch.model_validate_json(content)
        except (ValidationError, Exception):
            batch = PreferenceScoreBatch()

        by_id = {score.room_id: score for score in batch.scores}
        for room in rooms:
            by_id.setdefault(
                room.room_id,
                PreferenceScore(room_id=room.room_id, score=0.5, reason="偏好评分不可用，使用中性分。"),
            )
        return by_id
