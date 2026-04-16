from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import db
from routes.user import router as user_router
from routes.trip import router as trip_router
from routes.payment import router as payment_router
from routes.review import router as review_router
from routes.wishlist import router as wishlist_router
from routes.admin import router as admin_router

app = FastAPI(title="TripSync API", version="2.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router, prefix="/users", tags=["Users"])
app.include_router(trip_router, tags=["Trips"])
app.include_router(payment_router, prefix="/payments", tags=["Payments"])
app.include_router(review_router, tags=["Reviews"])
app.include_router(wishlist_router, tags=["Wishlist"])
app.include_router(admin_router, tags=["Admin"])

@app.get("/")
async def root():
    return {"message": "TripSync API v2.1 is running 🚀"}

@app.get("/health")
async def health_check():
    """
    Health check endpoint used by UptimeRobot to keep the service alive 24/7.
    """
    try:
        await db.command("ping")
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    return {"status": "ok", "database": db_status}
