from fastapi import APIRouter, HTTPException, status
from models import UserCreate, UserLogin, UserUpdate
from database import db
from bson import ObjectId
from bson.errors import InvalidId
import bcrypt

router = APIRouter()

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(user: UserCreate):
    existing_user = await db.users.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    user_dict = user.model_dump()
    user_dict["password"] = get_password_hash(user_dict["password"])
    # Verification fields stored in DB but NOT in pydantic model to prevent self-setting
    user_dict["is_verified"] = False
    user_dict["verification_status"] = "unverified"

    new_user = await db.users.insert_one(user_dict)
    return {"message": "User created successfully", "user_id": str(new_user.inserted_id)}

@router.post("/login")
async def login(user: UserLogin):
    db_user = await db.users.find_one({"email": user.email})
    if not db_user:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    if not verify_password(user.password, db_user["password"]):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    return {
        "message": "Login successful",
        "user_id": str(db_user["_id"]),
        "name": db_user.get("name", ""),
        "is_verified": db_user.get("is_verified", False),
        "verification_status": db_user.get("verification_status", "unverified")
    }

@router.get("/{user_id}")
async def get_user(user_id: str):
    try:
        obj_id = ObjectId(user_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid user_id format")

    user = await db.users.find_one({"_id": obj_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user["_id"] = str(user["_id"])
    user.pop("password", None)  # Never expose password
    return {"user": user}

@router.put("/{user_id}")
async def update_user(user_id: str, update: UserUpdate):
    try:
        obj_id = ObjectId(user_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid user_id format")

    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided to update")

    result = await db.users.update_one({"_id": obj_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": "Profile updated successfully"}

@router.post("/{user_id}/request-verification", status_code=status.HTTP_200_OK)
async def request_verification(user_id: str):
    """User requests host verification — sets status to 'pending'."""
    try:
        obj_id = ObjectId(user_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid user_id format")

    user = await db.users.find_one({"_id": obj_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    current_status = user.get("verification_status", "unverified")
    if current_status == "verified":
        raise HTTPException(status_code=400, detail="User is already verified")
    if current_status == "pending":
        raise HTTPException(status_code=400, detail="Verification already pending review")

    await db.users.update_one(
        {"_id": obj_id},
        {"$set": {"verification_status": "pending", "is_verified": False}}
    )
    return {"message": "Verification request submitted. You'll be notified once reviewed."}
