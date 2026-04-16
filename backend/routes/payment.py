import os
import razorpay
from fastapi import APIRouter, HTTPException, status
from models import OrderCreateRequest, PaymentVerifyRequest
from database import db
from bson import ObjectId
from bson.errors import InvalidId

router = APIRouter()

# Initialize Client
razorpay_client = razorpay.Client(
    auth=(os.getenv("RAZORPAY_KEY_ID"), os.getenv("RAZORPAY_KEY_SECRET"))
)

@router.post("/create-order")
async def create_order(request: OrderCreateRequest):
    try:
        user_obj_id = ObjectId(request.user_id)
        trip_obj_id = ObjectId(request.trip_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    trip = await db.trips.find_one({"_id": trip_obj_id})
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
        
    # Check if duplicate exists before creating payment order
    existing = await db.trip_members.find_one({
        "user_id": request.user_id,
        "trip_id": request.trip_id
    })
    if existing:
        raise HTTPException(status_code=400, detail="User already joined this trip")
        
    budget = float(trip.get("budget", 0))
    if budget <= 0:
        raise HTTPException(status_code=400, detail="Trip is free; no payment required")

    amount_in_paise = int(budget * 100)
    order_data = {
        "amount": amount_in_paise,
        "currency": "INR",  
        "receipt": f"rn_{request.user_id[:5]}_{request.trip_id[:5]}"
    }

    try:
        order = razorpay_client.order.create(data=order_data)
        return {"order_id": order["id"], "amount": amount_in_paise, "currency": "INR"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Razorpay error: {str(e)}")

@router.post("/verify-payment")
async def verify_payment(request: PaymentVerifyRequest):
    params_dict = {
        "razorpay_order_id": request.razorpay_order_id,
        "razorpay_payment_id": request.razorpay_payment_id,
        "razorpay_signature": request.razorpay_signature
    }

    try:
        razorpay_client.utility.verify_payment_signature(params_dict)
    except razorpay.errors.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Payment signature verification failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verification error: {str(e)}")

    existing = await db.trip_members.find_one({
        "user_id": request.user_id,
        "trip_id": request.trip_id
    })

    if not existing:
        await db.trip_members.insert_one({
            "user_id": request.user_id,
            "trip_id": request.trip_id,
            "payment_id": request.razorpay_payment_id
        })
        # Keep participant count in sync
        try:
            await db.trips.update_one(
                {"_id": ObjectId(request.trip_id)},
                {"$inc": {"current_participants": 1}}
            )
        except Exception:
            pass

    return {"message": "Payment verified and trip joined successfully"}
