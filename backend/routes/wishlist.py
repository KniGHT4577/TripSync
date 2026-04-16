from fastapi import APIRouter, HTTPException, status
from models import WishlistItem
from database import db
from bson import ObjectId
from bson.errors import InvalidId

router = APIRouter()

@router.post("/wishlist", status_code=status.HTTP_201_CREATED)
async def add_to_wishlist(item: WishlistItem):
    existing = await db.wishlist.find_one({
        "user_id": item.user_id,
        "trip_id": item.trip_id
    })
    if existing:
        raise HTTPException(status_code=400, detail="Trip already in wishlist")
    
    await db.wishlist.insert_one(item.model_dump())
    return {"message": "Added to wishlist"}

@router.delete("/wishlist/{user_id}/{trip_id}")
async def remove_from_wishlist(user_id: str, trip_id: str):
    result = await db.wishlist.delete_one({
        "user_id": user_id,
        "trip_id": trip_id
    })
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Wishlist item not found")
    return {"message": "Removed from wishlist"}

@router.get("/wishlist/{user_id}")
async def get_wishlist(user_id: str):
    cursor = db.wishlist.find({"user_id": user_id})
    trip_ids = []
    async for doc in cursor:
        trip_ids.append(doc["trip_id"])
    return {"wishlist": trip_ids}
