from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health():
    """健康检查。"""
    return {"status": "ok"}
