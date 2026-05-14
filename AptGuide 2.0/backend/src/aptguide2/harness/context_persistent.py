from __future__ import annotations

from typing import Any

from aptguide2.harness.contracts import AptGuideRequest, ConversationFrame


class PersistentContextStore:
    """Redis + MySQL backed context store for production use."""

    def __init__(self, redis_store: Any, session_repository: Any = None) -> None:
        self.redis_store = redis_store
        self.session_repository = session_repository

    def load(self, request: AptGuideRequest) -> ConversationFrame:
        """Sync load — for backward compatibility with tests."""
        import asyncio

        return asyncio.run(self.load_async(request))

    async def load_async(self, request: AptGuideRequest) -> ConversationFrame:
        """Async load from Redis, fallback to MySQL, fallback to new frame."""
        if not request.session_id:
            return ConversationFrame(
                session_id=request.session_id,
                request_id=request.request_id,
                user_id=request.user_id,
                message=request.message,
                action=request.action,
            )

        # Try Redis first
        payload = await self.redis_store.load_session(request.session_id)

        # Fallback to MySQL
        if payload is None and self.session_repository is not None:
            payload = await self.session_repository.load_frame(request.session_id)

        if payload:
            frame = ConversationFrame.model_validate(payload)
            frame.request_id = request.request_id
            frame.user_id = request.user_id
            frame.message = request.message
            frame.action = request.action

            # Rehydrate pending action from Redis if not in frame
            if frame.pending_action is None and request.action:
                confirmation_id = request.action.get("confirmation_id")
                if confirmation_id:
                    pending = await self.redis_store.load_pending_action(confirmation_id)
                    if pending:
                        frame.pending_action = pending

            return frame

        return ConversationFrame(
            session_id=request.session_id,
            request_id=request.request_id,
            user_id=request.user_id,
            message=request.message,
            action=request.action,
        )

    def save(self, frame: ConversationFrame) -> None:
        """Sync save — for backward compatibility with tests."""
        import asyncio

        return asyncio.run(self.save_async(frame))

    async def save_async(self, frame: ConversationFrame) -> None:
        """Async save to Redis and MySQL."""
        if not frame.session_id:
            return

        payload = frame.model_dump(mode="json")

        # Save to Redis
        await self.redis_store.save_session(frame.session_id, payload)

        # Save pending action if exists
        if frame.pending_action:
            confirmation_id = frame.pending_action.get("confirmation_id")
            if confirmation_id:
                await self.redis_store.save_pending_action(confirmation_id, frame.pending_action)

        # Save to MySQL if repository available
        if self.session_repository is not None:
            await self.session_repository.save_frame(frame)
