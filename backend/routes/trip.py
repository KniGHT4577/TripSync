from fastapi import APIRouter, status, HTTPException
from typing import Optional
from models import TripCreate, TripJoin
from database import db
from bson import ObjectId
from bson.errors import InvalidId

router = APIRouter()

@router.post("/trip", status_code=status.HTTP_201_CREATED)
async def create_trip(trip: TripCreate):
    # ── Host Verification Gate ─────────────────────────────────
    try:
        host_obj_id = ObjectId(trip.host_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid host_id format")

    host = await db.users.find_one({"_id": host_obj_id})
    if not host:
        raise HTTPException(status_code=404, detail="Host user not found")
    if not host.get("is_verified", False):
        raise HTTPException(
            status_code=403,
            detail="You must be a verified host to create trips. Apply for verification on your profile page."
        )
    # ──────────────────────────────────────────────────────────

    trip_dict = trip.model_dump()
    trip_dict["current_participants"] = 0
    new_trip = await db.trips.insert_one(trip_dict)
    return {"message": "Trip created successfully", "trip_id": str(new_trip.inserted_id)}

@router.get("/trips/my-trips")
async def get_my_trips(user_id: str):
    # Hosted trips
    hosted_cursor = db.trips.find({"host_id": user_id})
    hosted_trips = []
    async for doc in hosted_cursor:
        doc["_id"] = str(doc["_id"])
        doc["is_joined"] = True
        hosted_trips.append(doc)

    # Joined trips
    joined_cursor = db.trip_members.find({"user_id": user_id})
    joined_trip_ids = []
    async for member in joined_cursor:
        try:
            joined_trip_ids.append(ObjectId(member["trip_id"]))
        except InvalidId:
            pass

    joined_trips = []
    if joined_trip_ids:
        trips_cursor = db.trips.find({"_id": {"$in": joined_trip_ids}})
        async for doc in trips_cursor:
            doc["_id"] = str(doc["_id"])
            doc["is_joined"] = True
            joined_trips.append(doc)

    return {"hosted": hosted_trips, "joined": joined_trips}

@router.get("/trips")
async def get_trips(user_id: Optional[str] = None):
    cursor = db.trips.find({})
    trips = []

    joined_trip_ids = set()
    if user_id:
        joined_cursor = db.trip_members.find({"user_id": user_id})
        async for member in joined_cursor:
            joined_trip_ids.add(member["trip_id"])

    async for document in cursor:
        document["_id"] = str(document["_id"])
        document["is_joined"] = document["_id"] in joined_trip_ids
        trips.append(document)

    return {"trips": trips}

@router.get("/trip/{trip_id}")
async def get_trip(trip_id: str):
    try:
        obj_id = ObjectId(trip_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid trip_id format")

    trip = await db.trips.find_one({"_id": obj_id})
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    trip["_id"] = str(trip["_id"])
    return {"trip": trip}

@router.post("/join", status_code=status.HTTP_201_CREATED)
async def join_trip(join_request: TripJoin):
    try:
        user_obj_id = ObjectId(join_request.user_id)
        trip_obj_id = ObjectId(join_request.trip_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid user_id or trip_id format")

    user = await db.users.find_one({"_id": user_obj_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    trip = await db.trips.find_one({"_id": trip_obj_id})
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    # Check max participants
    max_p = trip.get("max_participants")
    current_p = trip.get("current_participants", 0)
    if max_p and current_p >= max_p:
        raise HTTPException(status_code=400, detail="Trip is full")

    # Prevent host from joining their own trip
    if trip.get("host_id") == join_request.user_id:
        raise HTTPException(status_code=400, detail="You cannot join your own trip")

    existing = await db.trip_members.find_one({
        "user_id": join_request.user_id,
        "trip_id": join_request.trip_id
    })
    if existing:
        raise HTTPException(status_code=400, detail="User already joined this trip")

    await db.trip_members.insert_one(join_request.model_dump())

    # Increment participant count
    await db.trips.update_one(
        {"_id": trip_obj_id},
        {"$inc": {"current_participants": 1}}
    )

    return {"message": "Successfully joined trip"}

@router.delete("/join/{user_id}/{trip_id}", status_code=status.HTTP_200_OK)
async def leave_trip(user_id: str, trip_id: str):
    """Leave a trip you've joined."""
    # Verify membership exists
    existing = await db.trip_members.find_one({"user_id": user_id, "trip_id": trip_id})
    if not existing:
        raise HTTPException(status_code=404, detail="You are not a member of this trip")

    # Check it's not the host's own trip
    try:
        trip_obj_id = ObjectId(trip_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid trip_id format")

    trip = await db.trips.find_one({"_id": trip_obj_id})
    if trip and trip.get("host_id") == user_id:
        raise HTTPException(status_code=400, detail="Hosts cannot leave their own trip. Delete the trip instead.")

    await db.trip_members.delete_one({"user_id": user_id, "trip_id": trip_id})

    # Decrement participant count (min 0)
    await db.trips.update_one(
        {"_id": trip_obj_id, "current_participants": {"$gt": 0}},
        {"$inc": {"current_participants": -1}}
    )

    return {"message": "Successfully left the trip"}

@router.get("/trip-members/{trip_id}")
async def get_trip_members(trip_id: str):
    """Return trip members enriched with name and city."""
    cursor = db.trip_members.find({"trip_id": trip_id})
    members = []
    async for doc in cursor:
        member_info = {
            "user_id": doc["user_id"],
            "name": "Traveler",
            "city": None,
            "initials": "T"
        }
        # Enrich with user data
        try:
            user_obj = ObjectId(doc["user_id"])
            user = await db.users.find_one({"_id": user_obj}, {"name": 1, "city": 1})
            if user:
                name = user.get("name", "Traveler")
                member_info["name"] = name
                member_info["city"] = user.get("city")
                member_info["initials"] = "".join(p[0].upper() for p in name.split()[:2])
        except (InvalidId, Exception):
            pass
        members.append(member_info)
    return {"members": members}

@router.get("/stats")
async def get_stats():
    """Platform statistics for the home page"""
    trips_count = await db.trips.count_documents({})
    users_count = await db.users.count_documents({})
    # Count unique locations as destinations
    pipeline = [{"$group": {"_id": "$location"}}, {"$count": "total"}]
    dest_result = await db.trips.aggregate(pipeline).to_list(1)
    destinations = dest_result[0]["total"] if dest_result else 0
    return {"trips": trips_count, "users": users_count, "destinations": destinations}
