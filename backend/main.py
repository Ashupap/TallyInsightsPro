from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tally_api import TallyAPIClient
from src.auth import authenticate_user as auth_user

app = FastAPI(title="Tally Prime Analytics API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LoginRequest(BaseModel):
    username: str
    password: str
    tally_server: str

class LoginResponse(BaseModel):
    success: bool
    message: str
    user: Optional[dict] = None

@app.post("/api/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    success = auth_user(request.username, request.password, request.tally_server)
    
    if success:
        return LoginResponse(
            success=True,
            message="Login successful",
            user={
                "username": request.username,
                "role": "Admin",
                "tally_server": request.tally_server
            }
        )
    else:
        return LoginResponse(
            success=False,
            message="Invalid credentials or unable to connect to Tally server"
        )

@app.get("/api/tally/test-connection")
async def test_connection(tally_server: str):
    client = TallyAPIClient(tally_server)
    is_connected = client.test_connection()
    
    return {
        "connected": is_connected,
        "server": tally_server
    }

@app.get("/api/dashboard/stats")
async def get_dashboard_stats(tally_server: str):
    client = TallyAPIClient(tally_server)
    
    return {
        "sales_today": "₹0",
        "sales_delta": "0%",
        "stock_items": "0",
        "stock_delta": "0",
        "active_customers": "0",
        "customers_delta": "0",
        "outstanding": "₹0",
        "outstanding_delta": "₹0"
    }

@app.get("/api/alerts")
async def get_alerts():
    return {
        "alerts": [
            {"type": "warning", "message": "3 items below reorder level", "icon": "📦"},
            {"type": "info", "message": "GST filing due in 5 days", "icon": "💳"}
        ]
    }

@app.get("/")
async def root():
    return {"message": "Tally Prime Analytics API", "status": "running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
