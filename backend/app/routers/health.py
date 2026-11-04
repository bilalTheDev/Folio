from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/")
async def root():
    return {"message": "Hello Folio"}


@router.get("/health")
async def health():
    return {"status": "ok"}
