from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def admin_dashboard():
    return {"msg": "Admin Dashboard"}
