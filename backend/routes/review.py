from fastapi import APIRouter, HTTPException, status
from models import ReviewCreate
from database import db
from bson import ObjectId
from bson.errors import InvalidId

router = APIRouter()

@router.post("/reviews", status_code=status.HTTP_201_CREATED)
async def create_review(review: ReviewCreate):
    try:
        host_obj_id = ObjectId(review.host_id)
        reviewer_obj_id = ObjectId(review.reviewer_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    host = await db.users.find_one({"_id": host_obj_id})
    if not host:
        raise HTTPException(status_code=404, detail="Host not found")
        
    reviewer = await db.users.find_one({"_id": reviewer_obj_id})
    if not reviewer:
        raise HTTPException(status_code=404, detail="Reviewer not found")

    review_dict = review.model_dump()
    review_dict["reviewer_name"] = reviewer.get("name", "Anonymous")
    
    await db.host_reviews.insert_one(review_dict)
    return {"message": "Review added successfully"}

@router.get("/reviews/{host_id}")
async def get_reviews(host_id: str):
    cursor = db.host_reviews.find({"host_id": host_id})
    reviews = []
    total_rating = 0
    count = 0
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        reviews.append(doc)
        total_rating += doc.get("rating", 0)
        count += 1
        
    average_rating = round(total_rating / count, 1) if count > 0 else 0
    return {"reviews": reviews, "average_rating": average_rating, "total_reviews": count}
