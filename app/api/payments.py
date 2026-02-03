from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def read_payments():
    return [{"id": 1, "status": "paid"}]
