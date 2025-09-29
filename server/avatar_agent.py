import os
import asyncio
import uuid
from dotenv import load_dotenv

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions, RoomOutputOptions
from livekit.plugins import (
    #openai,
    tavus,
    #silero, 
    google,
)

load_dotenv()

TAVUS_API_KEY = os.getenv("TAVUS_API_KEY")
TAVUS_REPLICA_ID = os.getenv("TAVUS_REPLICA_ID")
TAVUS_PERSONA_ID = os.getenv("TAVUS_PERSONA_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

class VideoAssistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="You are a helpful voice assistant with live video input from your user.",
            llm=google.beta.realtime.RealtimeModel(
                model="gemini-2.0-flash-exp",
                voice="Puck",
                temperature=0.8,
                api_key=GOOGLE_API_KEY,
                modalities=["AUDIO"]  # Only AUDIO is valid for now
            ),
        )

async def entrypoint(ctx: agents.JobContext):
    room_name = getattr(ctx, 'room', None)
    print(f"[avatar_agent] starting for room={room_name}")
    
    # Check if Google API key is available
    if not GOOGLE_API_KEY:
        print("[avatar_agent] WARNING: GOOGLE_API_KEY not found in environment variables!")
        print("[avatar_agent] Please set GOOGLE_API_KEY in your .env file")
        return 
    else:
        print(f"[avatar_agent] Google API key loaded: {GOOGLE_API_KEY[:5]}...")
    
    await ctx.connect()
    print("[avatar_agent] connected")

    # Create the AI agent session
    session = AgentSession()
    print("[avatar_agent] created AI agent session")
    # session = AgentSession(
    #     stt=openai.STT(
    #         api_key=OPENAI_API_KEY,
    #         model="whisper-1"
    #     ),
    #     llm=openai.LLM(
    #         api_key=OPENAI_API_KEY,
    #         model="gpt-4o"
    #     ),
    #     tts=openai.TTS(
    #         api_key=OPENAI_API_KEY,
    #         model="tts-1",
    #         voice="alloy"
    #     ),
    #     vad=silero.VAD.load()
    # )
    #print("[avatar_agent] created AI agent session with STT, LLM, TTS, and VAD")

    # Create Tavus avatar session for visual representation
    # Use unique identity to avoid stuck session issues
    avatar_identity = f"ai-assistant-{uuid.uuid4().hex[:8]}"
    avatar = tavus.AvatarSession(
        api_key=TAVUS_API_KEY,
        replica_id=TAVUS_REPLICA_ID,
        persona_id=TAVUS_PERSONA_ID,
        avatar_participant_name=avatar_identity
    )
    print("[avatar_agent] created Tavus avatar session")
    print(f"[avatar_agent] Tavus config: replica_id={TAVUS_REPLICA_ID}, persona_id={TAVUS_PERSONA_ID}")

    # Start the Tavus avatar first
    print(f"[avatar_agent] starting Tavus avatar for room: {room_name}")
    try:
        await avatar.start(session, room=ctx.room)
        print("[avatar_agent] ✅ Tavus avatar started successfully")
    except Exception as e:
        print(f"[avatar_agent] ❌ Error starting Tavus avatar: {e}")
        import traceback
        print(f"[avatar_agent] Tavus error traceback: {traceback.format_exc()}")

    # Start the AI agent session
    print("[avatar_agent] starting AI agent session...")
    try:
        await session.start(
            agent=VideoAssistant(),
            room=ctx.room,
            room_input_options=RoomInputOptions(
                video_enabled=True,
            ),
        )
        print("[avatar_agent] ✅ AI agent session started with vision enabled")
    except Exception as e:
        print(f"[avatar_agent] ❌ Error starting AI agent session: {e}")
        import traceback
        print(f"[avatar_agent] Session error traceback: {traceback.format_exc()}")
        return  # Exit early if session fails to start

    # Generate initial greeting with comprehensive error handling
    print("[avatar_agent] generating initial greeting...")
    try:
        print("[avatar_agent] Attempting to generate reply...")
        await session.generate_reply(
            instructions="Greet the user warmly and offer your assistance. Keep it brief and friendly."
        )
        print("[avatar_agent] ✅ Initial greeting sent successfully")
    except Exception as e:
        print(f"[avatar_agent] ❌ Error generating initial greeting: {e}")
        print(f"[avatar_agent] Error type: {type(e).__name__}")
        import traceback
        print(f"[avatar_agent] Traceback: {traceback.format_exc()}")
        
        # Try a simpler approach
        try:
            print("[avatar_agent] Attempting fallback greeting...")
            await session.say("Hello! I'm your AI assistant. How can I help you today?")
            print("[avatar_agent] ✅ Fallback greeting sent")
        except Exception as e2:
            print(f"[avatar_agent] ❌ Error with fallback greeting: {e2}")
            print(f"[avatar_agent] Fallback error type: {type(e2).__name__}")
            print(f"[avatar_agent] Fallback traceback: {traceback.format_exc()}")

    # Monitor for audio events
    async def monitor_audio():
        while True:
            await asyncio.sleep(10)  # Check every 10 seconds
            participants = list(ctx.room.remote_participants.values())
            print(f"[avatar_agent] Room has {len(participants)} participants:")
            for p in participants:
                print(f"  - {p.identity} ({p.name}): mic={p.is_microphone_enabled}, cam={p.is_camera_enabled}")
    
    # Start monitoring in background
    asyncio.create_task(monitor_audio())
    
    # Monitor for audio events
    @ctx.room.on("track_subscribed")
    def on_track_subscribed(track, publication, participant):
        print(f"[avatar_agent] Track subscribed: {track.kind} from {participant.identity}")
        if track.kind == "audio":
            print(f"[avatar_agent] Audio track received from {participant.identity}")
            print(f"[avatar_agent] Audio track details: source={track.source}, sid={track.sid}")
    
    @ctx.room.on("track_published")
    def on_track_published(publication, participant):
        print(f"[avatar_agent] Track published: {publication.kind} from {participant.identity}")
        if publication.kind == "audio":
            print(f"[avatar_agent] Audio track published from {participant.identity}")
            print(f"[avatar_agent] Audio track details: source={publication.source}, sid={publication.sid}")
    
    @ctx.room.on("track_unsubscribed")
    def on_track_unsubscribed(track, publication, participant):
        print(f"[avatar_agent] Track unsubscribed: {track.kind} from {participant.identity}")
    
    @ctx.room.on("participant_connected")
    def on_participant_connected(participant):
        print(f"[avatar_agent] Participant connected: {participant.identity}")
        # Subscribe to the new participant's tracks
        print(f"[avatar_agent] Subscribing to tracks from new participant: {participant.identity}")
        asyncio.create_task(participant.subscribe())
    
    @ctx.room.on("participant_disconnected")
    def on_participant_disconnected(participant):
        print(f"[avatar_agent] Participant disconnected: {participant.identity}")

    print("[avatar_agent] avatar session active, monitoring for audio...")
    print("[avatar_agent] Room participants:", [p.identity for p in ctx.room.remote_participants.values()])

    try:
        while True:
            await asyncio.sleep(1)
    finally:
        print("[avatar_agent] shutting down")
        await session.aclose()

# 👇 THIS is what enables:  `python avatar_agent.py dev|start|connect --room demo`
if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))

# you physically run this command: python avatar_agent.py connect --room room-metyln77-lu5x8d
# However, when we try to "automate it", we need to call this file from server.py, meaning it will look for - if __name__ == "__main__":
# parses the room name from the command line and passes it to the entrypoint function.

# python avatar_agent.py connect --room test_room - testing in the terminal