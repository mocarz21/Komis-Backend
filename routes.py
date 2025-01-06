from fastapi import APIRouter
from controllers.cars import router as cars_router
from controllers.users import router as users_router
from controllers.drives import router as drives_router

router = APIRouter()

# Dodajemy routery z kontrolerami
router.include_router(cars_router)
router.include_router(users_router)
router.include_router(drives_router)