from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def read_orders():
    return [{"id": 1, "total": 100.0}]
