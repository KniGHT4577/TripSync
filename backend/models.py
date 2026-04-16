from pydantic import BaseModel, EmailStr
from typing import Optional, List

class HealthResponse(BaseModel):
    status: str
    database: str

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    city: str
    bio: Optional[str] = None
    interests: Optional[List[str]] = []

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    city: Optional[str] = None
    bio: Optional[str] = None
    interests: Optional[List[str]] = None

class TripCreate(BaseModel):
    title: str
    location: str
    date: str
    end_date: Optional[str] = None
    budget: float
    host_id: str
    description: Optional[str] = None
    itinerary: Optional[str] = None
    category: Optional[str] = "other"
    max_participants: Optional[int] = None
    contact_info: Optional[str] = None

class TripJoin(BaseModel):
    user_id: str
    trip_id: str

class OrderCreateRequest(BaseModel):
    trip_id: str
    user_id: str

class PaymentVerifyRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    user_id: str
    trip_id: str

class ReviewCreate(BaseModel):
    host_id: str
    reviewer_id: str
    rating: int
    comment: Optional[str] = None

class WishlistItem(BaseModel):
    user_id: str
    trip_id: str

class VerificationRequest(BaseModel):
    user_id: str
