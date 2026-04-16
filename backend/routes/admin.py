from fastapi import APIRouter, HTTPException, Header, status
from database import db
from bson import ObjectId
from bson.errors import InvalidId
import os

router = APIRouter()

ADMIN_SECRET = os.getenv("ADMIN_SECRET_KEY", "tripsync-admin-secret-2024")

def verify_admin_key(x_admin_key: str = Header(None)):
    if x_admin_key != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Invalid admin key")

@router.post("/admin/verify/{user_id}", status_code=status.HTTP_200_OK)
async def verify_host(user_id: str, x_admin_key: str = Header(None)):
    """
    Admin endpoint to approve host verification.
    Requires X-Admin-Key header matching ADMIN_SECRET_KEY env var.
    """
    verify_admin_key(x_admin_key)

    try:
        obj_id = ObjectId(user_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid user_id format")

    user = await db.users.find_one({"_id": obj_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.get("is_verified"):
        return {"message": f"{user.get('name', user_id)} is already verified"}

    await db.users.update_one(
        {"_id": obj_id},
        {"$set": {"is_verified": True, "verification_status": "verified"}}
    )
    return {"message": f"✅ {user.get('name', user_id)} has been verified as a host"}

@router.post("/admin/unverify/{user_id}", status_code=status.HTTP_200_OK)
async def unverify_host(user_id: str, x_admin_key: str = Header(None)):
    """Admin endpoint to revoke host verification."""
    verify_admin_key(x_admin_key)

    try:
        obj_id = ObjectId(user_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid user_id format")

    await db.users.update_one(
        {"_id": obj_id},
        {"$set": {"is_verified": False, "verification_status": "unverified"}}
    )
    return {"message": "Host verification revoked"}

@router.get("/admin/pending")
async def get_pending_verifications(x_admin_key: str = Header(None)):
    """List all users with pending verification requests."""
    verify_admin_key(x_admin_key)

    cursor = db.users.find(
        {"verification_status": "pending"},
        {"password": 0}  # Never return passwords
    )
    users = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        users.append(doc)
    return {"pending_users": users, "count": len(users)}

@router.get("/admin/all-users")
async def get_all_users(x_admin_key: str = Header(None)):
    """List all users with their verification status."""
    verify_admin_key(x_admin_key)

    cursor = db.users.find({}, {"password": 0})
    users = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        users.append(doc)
    return {"users": users, "count": len(users)}
