import os
import subprocess
import asyncio
import sys
import requests
import uuid
import random
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Optional

# LiveKit Python server SDK
from livekit import api  # pip install livekit-api

load_dotenv()

LIVEKIT_URL = os.getenv("LIVEKIT_URL")  # not strictly needed for token; handy to expose to FE if you want
LK_API_KEY = os.getenv("LIVEKIT_API_KEY")
LK_API_SECRET = os.getenv("LIVEKIT_API_SECRET")
TAVUS_API_KEY = os.getenv("TAVUS_API_KEY")
TAVUS_REPLICA_ID = os.getenv("TAVUS_REPLICA_ID")
TAVUS_PERSONA_ID = os.getenv("TAVUS_PERSONA_ID")

if not (LK_API_KEY and LK_API_SECRET):
    raise RuntimeError("LIVEKIT_API_KEY and LIVEKIT_API_SECRET must be set in .env")

if not (TAVUS_API_KEY and TAVUS_REPLICA_ID and TAVUS_PERSONA_ID):
    print("Warning: Tavus credentials not fully configured. Avatar features will be disabled.")

app = FastAPI(title="LiveKit Token Server")

# CORS configuration - allow all origins for now
# TODO: Update this with your actual frontend domains after deployment
allowed_origins = ["*"]  # Allow all origins for initial deployment

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

class JoinRoomRequest(BaseModel):
    room_name: str
    participant_name: str
    mic_enabled: bool = True
    camera_enabled: bool = True
    invite_avatar: bool = False  # New field to optionally invite avatar
    language: str = "en-US"  # Language code for AI assistant
    device_id: Optional[str] = None  # Persistent device ID for memory

class InviteAvatarRequest(BaseModel):
    room_name: str
    avatar_name: str = "AI Assistant"

class InitiateCallRequest(BaseModel):
    room_name: str
    caller_name: str
    target_user_id: Optional[str] = None  # Optional: send to specific user

class SendNotificationRequest(BaseModel):
    to: str
    title: str
    body: str
    data: dict
    categoryId: Optional[str] = None
    sound: str = "default"
    priority: str = "high"

class CallResponse(BaseModel):
    call_id: str
    room_name: str
    caller_name: str
    status: str
    created_at: str

class RegisterTokenRequest(BaseModel):
    expo_push_token: str
    user_id: Optional[str] = None
    device_name: Optional[str] = None

# Store running avatar processes
avatar_processes = {}  # {room_name: process}

# Background task to monitor and clean up dead avatar processes
async def cleanup_dead_processes():
    """Background task to clean up terminated avatar processes"""
    while True:
        await asyncio.sleep(5)  # Check every 5 seconds
        dead_rooms = []
        for room_name, process in avatar_processes.items():
            if process.poll() is not None:  # Process has ended
                dead_rooms.append(room_name)
                print(f"[server] Cleaned up dead avatar process for room: {room_name}")
        
        for room_name in dead_rooms:
            del avatar_processes[room_name]

# Start cleanup task on app startup
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(cleanup_dead_processes())
    print("[server] Started avatar process cleanup task")

# Store push tokens and active calls
push_tokens = {}  # {expo_push_token: {user_id, device_name, registered_at}}
active_calls = {}  # {call_id: CallResponse}

# Connection optimization settings
CONNECTION_TIMEOUT = 10  # seconds
AVATAR_WARMUP_DELAY = 0.5  # seconds

# Notification message variations - Student-focused invitations to chat with AI agent
NOTIFICATION_MESSAGES = [
    "Hey! Your AI study buddy is online and ready to help!",
    "Come chat with your AI tutor - they're waiting to assist you!",
    "Your AI learning companion is here! Let's study together!",
    "Ready for some AI-powered study help? Come online now!",
    "Your AI mentor is available! Time for a learning session!"
]

async def start_avatar_agent(room_name: str, language: str = "en-US", display_name: Optional[str] = None) -> bool:
    """
    Start an avatar agent process for the specified room.
    Returns True if successful, False otherwise.
    """
    try:
        print(f"[server] Starting avatar agent for room: {room_name}, language: {language}, user: {display_name or 'None'}...")
        if not (TAVUS_API_KEY and TAVUS_REPLICA_ID and TAVUS_PERSONA_ID):
            print("Tavus credentials not configured")
            return False
            
        # Check if avatar is already running for this room
        if room_name in avatar_processes:
            process = avatar_processes[room_name]
            if process.poll() is None:
                print(f"Avatar already running for room: {room_name}")
                return True
            else:
                # Process has ended, clean it up
                print(f"Cleaning up dead avatar process for room: {room_name}")
                del avatar_processes[room_name]
            
        # Set environment variables for the agent process
        env = os.environ.copy()
        env.update({
            "LIVEKIT_URL": LIVEKIT_URL,
            "LIVEKIT_API_KEY": LK_API_KEY,
            "LIVEKIT_API_SECRET": LK_API_SECRET,
            "TAVUS_API_KEY": TAVUS_API_KEY,
            "TAVUS_REPLICA_ID": TAVUS_REPLICA_ID,
            "TAVUS_PERSONA_ID": TAVUS_PERSONA_ID,
            "LANGUAGE": language,
            "USER_DISPLAY_NAME": display_name or "",  # Pass display name for memory
        })
        
        # Start the avatar agent process with virtual environment
        if os.name == 'nt':  # Windows
            # Use the current Python executable (which should be from the virtual environment)
            cmd = [
                sys.executable, 
                "avatar_agent.py", "connect",
                "--room", room_name
            ]
        else:  # Unix/Linux/Mac
            cmd = [
                sys.executable, 
                "avatar_agent.py", "connect",
                "--room", room_name
            ]
        
        print(f"Starting avatar agent with command: {' '.join(cmd)}")
        
        # Don't capture output - let it print directly to console
        process = subprocess.Popen(
            cmd,
            env=env,
            cwd=os.path.dirname(os.path.abspath(__file__)),  # Use server directory
            stdout=None,  # Print directly to console
            stderr=None,  # Print directly to console
            text=True
        )
        
        # Store the process
        avatar_processes[room_name] = process
        
        # Optimized startup delay for faster connection
        await asyncio.sleep(AVATAR_WARMUP_DELAY)
        
        # Check if process is still running
        if process.poll() is None:
            print(f"✅ Avatar agent started successfully for room: {room_name}")
            print(f"   Avatar agent logs will appear below...")
            return True
        else:
            print(f"❌ Avatar agent failed to start for room: {room_name}")
            return False
            
    except Exception as e:
        print(f"Error starting avatar agent: {str(e)}")
        return False

async def send_notification(notification_request: SendNotificationRequest) -> bool:
    """
    Send push notification via Expo Push API
    """
    try:
        message = {
            "to": notification_request.to,
            "title": notification_request.title,
            "body": notification_request.body,
            "data": notification_request.data,
            "sound": notification_request.sound,
            "priority": notification_request.priority
        }
        
        if notification_request.categoryId:
            message["categoryId"] = notification_request.categoryId
        
        response = requests.post(
            "https://exp.host/--/api/v2/push/send",
            json=message,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Accept-Encoding": "gzip, deflate"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("data", {}).get("status") == "ok":
                print(f"✅ Notification sent successfully to {notification_request.to}")
                return True
            else:
                print(f"❌ Notification failed: {result}")
                return False
        else:
            print(f"❌ HTTP error {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending notification: {str(e)}")
        return False

@app.get("/")
def health():
    return {"ok": True, "service": "livekit-token", "livekit_url": LIVEKIT_URL}

@app.post("/register-token")
async def register_push_token(request: RegisterTokenRequest):
    """
    Register a device's Expo push token for receiving notifications
    """
    try:
        push_tokens[request.expo_push_token] = {
            "user_id": request.user_id,
            "device_name": request.device_name,
            "registered_at": datetime.now().isoformat()
        }
        
        print(f"📱 Registered push token: {request.expo_push_token[:20]}...")
        print(f"   User ID: {request.user_id}")
        print(f"   Device: {request.device_name}")
        
        return {
            "status": "success",
            "message": "Push token registered successfully",
            "token_preview": f"{request.expo_push_token[:20]}...",
            "total_tokens": len(push_tokens)
        }
        
    except Exception as e:
        print(f"Error registering push token: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to register push token: {str(e)}")

@app.get("/token")
def token(roomName: str = "demo", identity: str = "", name: str = ""):
    """
    Mint a client join token.
    GET /token?roomName=demo&identity=abel[&name=Abel Tan]
    """
    try:
        identity = (identity or "").strip() or f"user-{os.urandom(3).hex()}"
        name = (name or identity).strip()

        # Grants: allow this identity to join the given room
        grants = api.VideoGrants(
            room_join=True,
            room=roomName,
        )

        # Build token with fluent API (current SDK style)
        token = (
            api.AccessToken(os.getenv("LIVEKIT_API_KEY"), os.getenv("LIVEKIT_API_SECRET"))
            .with_identity(identity)   # participant identity (unique per room)
            .with_name(name)           # display name shown in UIs
            .with_grants(grants)
        )

        return {
            "token": token.to_jwt(),
            "roomName": roomName,
            "identity": identity,
            "name": name,
            "livekitUrl": os.getenv("LIVEKIT_URL"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TOKEN_MINT_FAILED: {e}")

@app.post("/join-room")
async def join_room(request: JoinRoomRequest):
    """
    Create a room and return a token for joining.
    This endpoint handles room creation and token generation in one call.
    Optionally starts a Tavus avatar agent for the room.
    """
    try:
        # Generate a unique identity for the participant
        identity = f"{request.participant_name}-{os.urandom(4).hex()}"
        
        # Create video grant for the room
        grant = api.VideoGrants(
            room_join=True,
            room=request.room_name,
        )
        
        # Create access token
        at = api.AccessToken(LK_API_KEY, LK_API_SECRET)
        at.with_identity(identity)
        at.with_grants(grant)
        
        # Note: LiveKit rooms are created automatically when the first participant joins
        # So we don't need to explicitly create the room here
        
        response_data = {
            "token": at.to_jwt(),
            "room_name": request.room_name,
            "identity": identity,
            "livekit_url": LIVEKIT_URL,
            "participant_name": request.participant_name,
            "mic_enabled": request.mic_enabled,
            "camera_enabled": request.camera_enabled
        }

        # Start avatar agent in parallel with token generation for faster connection
        if request.invite_avatar:
            print(f"[server] Starting avatar with language: {request.language}, user: {request.participant_name}")
            # Start avatar agent asynchronously without waiting
            asyncio.create_task(start_avatar_agent(request.room_name, request.language, request.participant_name))
            response_data["avatar_invited"] = True  # Assume it will start
            response_data["avatar_name"] = "AI Assistant"
            response_data["avatar_status"] = "Starting..."
        else:
            response_data["avatar_invited"] = False
        
        return response_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create room and token: {str(e)}")

@app.post("/invite-avatar")
async def invite_avatar_to_room(request: InviteAvatarRequest):
    """
    Start a Tavus avatar agent for a room.
    This will spawn a separate process running the avatar agent.
    """
    try:
        if not (TAVUS_API_KEY and TAVUS_REPLICA_ID and TAVUS_PERSONA_ID):
            raise HTTPException(
                status_code=400, 
                detail="Tavus credentials not configured. Please set TAVUS_API_KEY, TAVUS_REPLICA_ID, and TAVUS_PERSONA_ID in your .env file"
            )

        avatar_started = await start_avatar_agent(request.room_name)
        
        if avatar_started:
            return {
                "success": True,
                "message": f"Avatar '{request.avatar_name}' invited to room '{request.room_name}'",
                "room_name": request.room_name,
                "avatar_name": request.avatar_name
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to start avatar agent"
            )

    except Exception as e:
        print(f"Error inviting avatar: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to invite avatar: {str(e)}"
        )

@app.get("/room-info/{room_name}")
async def get_room_info(room_name: str):
    """
    Get information about a specific room.
    """
    try:
        # Check if avatar is running for this room
        avatar_running = False
        if room_name in avatar_processes:
            process = avatar_processes[room_name]
            avatar_running = process.poll() is None  # None means still running
        
        return {
            "room_name": room_name,
            "livekit_url": LIVEKIT_URL,
            "status": "available",
            "avatar_running": avatar_running
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get room info: {str(e)}")

@app.post("/cleanup-avatar/{room_name}")
async def cleanup_avatar_process(room_name: str):
    """
    Manually clean up a stuck avatar process for a room.
    """
    try:
        if room_name in avatar_processes:
            process = avatar_processes[room_name]
            if process.poll() is None:
                # Process is still running, terminate it
                print(f"[server] Terminating avatar process for room: {room_name}")
                process.terminate()
                try:
                    process.wait(timeout=5)
                    print(f"[server] Avatar process terminated gracefully")
                except subprocess.TimeoutExpired:
                    print(f"[server] Force killing avatar process")
                    process.kill()
                    process.wait()
            del avatar_processes[room_name]
            return {
                "success": True,
                "message": f"Cleaned up avatar process for room: {room_name}"
            }
        else:
            return {
                "success": True,
                "message": f"No avatar process found for room: {room_name}"
            }
    except Exception as e:
        print(f"[server] Error cleaning up avatar: {str(e)}")
        return {
            "success": False,
            "error": f"Failed to cleanup avatar process: {str(e)}"
        }

@app.get("/active-avatars")
async def get_active_avatars():
    """
    Get list of active avatar processes for debugging.
    """
    active = {}
    for room_name, process in avatar_processes.items():
        active[room_name] = {
            "pid": process.pid,
            "is_running": process.poll() is None,
            "returncode": process.returncode
        }
    return {
        "active_avatars": active,
        "total_count": len(avatar_processes)
    }

@app.get("/test-tavus")
async def test_tavus_credentials():
    """
    Test endpoint to verify Tavus credentials are properly configured.
    """
    try:
        if not (TAVUS_API_KEY and TAVUS_REPLICA_ID and TAVUS_PERSONA_ID):
            return {
                "status": "error",
                "message": "Tavus credentials not fully configured",
                "credentials": {
                    "api_key": "Set" if TAVUS_API_KEY else "Missing",
                    "replica_id": "Set" if TAVUS_REPLICA_ID else "Missing", 
                    "persona_id": "Set" if TAVUS_PERSONA_ID else "Missing"
                }
            }
        
        # Test basic imports
        try:
            from livekit import agents
            from livekit.plugins import tavus
            imports_ok = True
        except ImportError as e:
            imports_ok = False
            import_error = str(e)
        
        return {
            "status": "success",
            "message": "Tavus credentials are configured",
            "credentials": {
                "api_key": f"Set (ends with ...{TAVUS_API_KEY[-4:]})",
                "replica_id": TAVUS_REPLICA_ID,
                "persona_id": TAVUS_PERSONA_ID
            },
            "imports": {
                "livekit_agents": imports_ok,
                "livekit_tavus_plugin": imports_ok,
                "error": import_error if not imports_ok else None
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error testing Tavus credentials: {str(e)}"
        }

@app.post("/initiate-call")
async def initiate_call(request: InitiateCallRequest):
    """Initiate a call and send notification to target device(s)"""
    try:
        # Generate unique call ID
        call_id = f"call_{uuid.uuid4().hex[:8]}"
        created_at = datetime.now().isoformat()
        
        # Create call object
        call = CallResponse(
            call_id=call_id,
            room_name=request.room_name,
            caller_name=request.caller_name,
            status="initiated",
            created_at=created_at
        )
        
        # Store the call
        active_calls[call_id] = call
        
        # Send notification to all registered devices (or specific user)
        target_tokens = []
        if request.target_user_id:
            # Send to specific user's tokens
            for token, data in push_tokens.items():
                if data.get("user_id") == request.target_user_id:
                    target_tokens.append(token)
        else:
            # Send to all registered tokens
            target_tokens = list(push_tokens.keys())
        
        if not target_tokens:
            return {
                "status": "warning",
                "message": "No devices available to receive the call",
                "call_id": call_id
            }
        
        # Send notifications
        sent_count = 0
        for token in target_tokens:
            try:
                # Select a random message variation for student-focused AI agent invitation
                random_message = random.choice(NOTIFICATION_MESSAGES)
                
                notification_request = SendNotificationRequest(
                    to=token,
                    title=f"{request.caller_name} wants to connect with you",
                    body=random_message,
                    data={
                        "type": "incoming_call",
                        "call_id": call_id,
                        "room_name": request.room_name,
                        "caller_name": request.caller_name,
                        "action": "answer_call"
                    },
                    categoryId="incoming-call",
                    sound="default",
                    priority="high"
                )
                
                await send_notification(notification_request)
                sent_count += 1
                
            except Exception as e:
                print(f"Failed to send call notification to token {token}: {str(e)}")
        
        print(f"📞 Call initiated: {request.caller_name} -> {request.room_name} (ID: {call_id})")
        print(f"📱 Notifications sent to {sent_count} device(s)")
        
        return {
            "status": "success",
            "message": f"Call initiated and notifications sent to {sent_count} device(s)",
            "call_id": call_id,
            "room_name": request.room_name,
            "caller_name": request.caller_name,
            "notifications_sent": sent_count
        }
        
    except Exception as e:
        print(f"Error initiating call: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to initiate call: {str(e)}")

@app.get("/active-calls")
async def get_active_calls():
    """Get all active calls"""
    return {
        "active_calls": list(active_calls.values()),
        "total_calls": len(active_calls)
    }

@app.get("/registered-tokens")
async def get_registered_tokens():
    """Get all registered push tokens (for debugging)"""
    return {
        "tokens": [
            {
                "token_preview": f"{token[:20]}...",
                "user_id": data.get("user_id"),
                "device_name": data.get("device_name"),
                "registered_at": data.get("registered_at")
            }
            for token, data in push_tokens.items()
        ],
        "total_tokens": len(push_tokens)
    }

# ============= Conversation Spark API =============

@app.get("/api/users")
async def get_all_users():
    """Get all unique users from Qdrant memory database"""
    try:
        from memory_service import get_memory_service
        memory_service = get_memory_service()
        
        # Get all memories to extract unique user IDs
        # Note: In production, you'd want a more efficient way to get unique users
        # For now, we'll use Qdrant's scroll API to get all points
        from qdrant_client import QdrantClient
        
        qdrant_url = os.getenv("QDRANT_URL")
        qdrant_api_key = os.getenv("QDRANT_API_KEY")
        
        if not qdrant_url or not qdrant_api_key:
            return {"users": []}
        
        client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
        
        # Scroll through all points to get unique user_ids
        points, _ = client.scroll(
            collection_name="studymate_memories",
            limit=1000,  # Adjust as needed
            with_payload=True,
            with_vectors=False
        )
        
        # Extract unique user_ids (which are now display names)
        user_names = set()
        for point in points:
            if point.payload and 'user_id' in point.payload:
                user_names.add(point.payload['user_id'])
        
        # Create user objects with basic info
        users = [
            {
                "id": user_name,
                "display_name": user_name
            }
            for user_name in sorted(user_names)
        ]
        
        return {"users": users, "total": len(users)}
        
    except Exception as e:
        print(f"Error fetching users: {e}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to fetch users: {str(e)}")

class ConversationStartersRequest(BaseModel):
    display_name: str

@app.post("/api/conversation-starters")
async def generate_conversation_starters(request: ConversationStartersRequest):
    """Generate conversation starter questions based on a user's memories"""
    try:
        from memory_service import get_memory_service
        import google.generativeai as genai
        
        memory_service = get_memory_service()
        display_name = request.display_name
        
        # Get all memories for this user (using display_name as user_id)
        memories = memory_service.get_all_memories(display_name)
        
        if not memories:
            return {
                "starters": [
                    "Hey! How's your studying going?",
                    "What subjects are you focusing on these days?",
                    "Need any study tips or motivation?"
                ],
                "user_info": f"{display_name} (no memory data yet)"
            }
        
        # Format memories into a context string
        memory_context = memory_service.format_memories_for_context(memories)
        
        # Use Gemini to generate conversation starters
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        prompt = f"""Based on this user's study session history, generate 5 specific, friendly conversation starter questions that another student could ask them to break the ice and build a study friendship.

User's Study History:
{memory_context}

Requirements:
1. Questions should be specific to topics they've studied
2. Casual and friendly tone (not formal)
3. Show genuine interest in their progress
4. Mix of questions about: their topics, challenges, progress, feelings
5. Keep each question under 15 words

Format: Return ONLY a JSON array of 5 strings, nothing else.
Example: ["How's your photosynthesis revision going?", "Need help with that algebra concept?", ...]"""

        response = model.generate_content(prompt)
        
        # Parse the JSON response
        import json
        import re
        
        # Extract JSON from response
        text = response.text.strip()
        # Remove markdown code blocks if present
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        
        starters = json.loads(text)
        
        return {
            "starters": starters,
            "user_info": display_name,
            "memory_count": len(memories)
        }
        
    except Exception as e:
        print(f"Error generating conversation starters: {e}")
        import traceback
        print(traceback.format_exc())
        
        # Return fallback starters
        return {
            "starters": [
                "Hey! How's your studying going?",
                "What subjects are you working on?",
                "Need any study help or tips?",
                "How are you feeling about your exams?",
                "Want to be study buddies?"
            ],
            "user_info": display_name,
            "error": "Using fallback questions"
        }

if __name__ == "__main__":
    import uvicorn
    # Use production settings when deployed
    is_production = os.getenv("RENDER") == "true" or os.getenv("ENVIRONMENT") == "production"
    
    uvicorn.run(
        "server:app",
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "3001")),
        reload=not is_production,  # Disable reload in production
        workers=1 if is_production else 1,  # Single worker for now
    )
