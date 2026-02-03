from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def read_coupons():
    return [{"code": "SAVE10", "discount": 10.0}]
