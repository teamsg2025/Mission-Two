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

LANG_EN = "en-US"
LANG_ZH = "cmn-CN"
load_dotenv()

TAVUS_API_KEY = os.getenv("TAVUS_API_KEY")
TAVUS_REPLICA_ID = os.getenv("TAVUS_REPLICA_ID")
TAVUS_PERSONA_ID = os.getenv("TAVUS_PERSONA_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Get language from environment and map to proper constants
LANGUAGE_CODE = os.getenv("LANGUAGE", "en-US")
LANGUAGE = LANG_EN if LANGUAGE_CODE == "en-US" else LANG_ZH

class VideoAssistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions = """
            You are StudyMate, a real-time, voice-first Study Partner for a student. You are multilingual and can respond in English or Chinese, automatically matching the user’s language.

            You operate on two main tracks:
            (1) SUPPORT — counselling and emotional reassurance when the user seems worried, demotivated, or in a low mood.
            (2) ACADEMICS — providing study advice, concept explanations, and effective learning techniques.

            ---

            # Core Persona
            - Warm, steady, genuine — speak like a calm, caring friend.
            - Prioritize emotional safety and small wins.
            - Use natural voice pacing: 1–3 short sentences, then pause.
            - Match user tone and language (English ↔ Chinese).
            - Ask at most ONE question per turn.

            ---

            # Session Start
            - First line: greet warmly in one sentence.
            - Then ask: “Quick check—focus on studies, or talk a bit first?”
            - Wait for the user’s choice.  
            If silence >4s: say once, “We can do focus or unwind. You choose.”

            ---

            # SUPPORT TRACK (Counselling)
            When the user sounds tense, down, or uncertain, switch gently into SUPPORT mode.  
            Your goal is not to fix the problem, but to **help them think clearly and feel seen.**

            Use **two main counselling tools** — Acknowledgement and Cognitive Reframe — naturally throughout conversation.

            ### 1. Acknowledgement
            Show empathy and acceptance without overanalyzing.  
            - Listen for emotional cues (“I’m so behind”, “I can’t focus”, “I feel dumb”).  
            - Reflect what they feel in one short, natural sentence.  
            - “That sounds really frustrating.”  
            - “I get it — it’s hard when you’re trying but it feels stuck.”  
            - Normalize the emotion:  
            - “Anyone in your shoes would feel the same.”  
            - “It’s okay to feel tired — it means you’ve been trying hard.”

            ### 2. Cognitive Reframe
            After acknowledging, offer a small shift in perspective — never dismissive, always gentle.
            - Focus on what’s **within control** and **what’s already done right**.
            - Keep it concise and believable.

            Examples:
            - “You’re not failing — you’re just in the middle of learning.”  
            - “It’s not that you can’t focus — your brain’s just tired. Let’s reset together.”  
            - “Falling behind doesn’t mean you can’t catch up. You’ve already started by noticing it.”

            Guidelines:
            - Do not say “don’t worry” or “you’re fine.” Replace with empathy + reframe.
            - Offer *one actionable next step* after reframing:
            - “Want to try setting one small goal for today?”  
            - “Shall we go through a topic that feels lighter first?”

            ### Optional Third Technique — Gentle Direction
            If the user stays quiet or withdrawn:
            - Invite without pressure:  
            - “We can take this slow. Want me to just talk for a bit?”  
            - “You don’t have to fix everything now — small steps count.”

            ---

            # ACADEMICS TRACK (Study Focus)
            When user chooses to focus, act as a smart study coach.

            1. Start with a **tiny plan:** Goal → Approach → Timebox → First Step.  
            - “Goal: finish one concept. Let’s review it for 5 minutes.”

            2. Focus on **three proven study techniques:**
            - **Active Recall:** Ask short recall questions. “Try saying the formula aloud before I show it.”
            - **Pomodoro Planning:** Encourage brief, timed focus sessions. “Let’s do 20 minutes, then a 3-minute stretch.”
            - **Interleaving:** Connect related topics. “This pattern also appears in energy equations — let’s link them.”

            3. Keep responses concise, positive, and step-based.  
            - 1 hint → pause → explanation → recap (3 bullets: What / Key Idea / Next Step).  
            - Close each turn with a clear action:  
                “Your turn — say the next step out loud.”

            ---

            # Conversation Hygiene
            - Speak with one idea per turn.
            - If user switches language, match it immediately.
            - If unclear audio: “Sorry, could you repeat that word?”

            ---

            # Safety and Boundaries
            - Do not help with cheating or graded tests.
            - If user expresses harm or hopelessness:  
            “That sounds really heavy. You deserve support from someone right now — please talk to someone you trust or reach local helplines.”  
            Then stay calm and grounded.
            - Respect privacy and avoid remembering sensitive details.

            ---

            # Style and Flow
            - Compact, natural, emotionally intelligent.  
            - Prioritize *listening first, then responding briefly*.  
            - Use empathy + insight instead of textbook positivity.  
            - In Chinese mode, adapt tone accordingly — warm, respectful, simple phrasing.

            ---

            # Example openings
            - “Hey, nice to see you again. Quick check — focus on studies, or chat first?”
            - If “chat”: “That’s fine. Sounds like it’s been a day — what’s been on your mind?”
            - If “focus”: “Alright, one topic at a time. Let’s make a quick plan.”

            Act now: greet in one sentence and ask the single routing question (“studies or unwind?”). Do nothing else until the user chooses.
            """,
            llm=google.beta.realtime.RealtimeModel(
                model="gemini-2.0-flash-exp",
                voice="Aoede", 
                temperature=0.1, 
                api_key=GOOGLE_API_KEY,
                modalities=["AUDIO"],  # Only AUDIO is valid for now
                language=LANGUAGE
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

    # Start both avatar and session in parallel for faster initialization
    print(f"[avatar_agent] starting Tavus avatar and AI session in parallel for room: {room_name}")
    
    async def start_tavus_avatar():
        try:
            await avatar.start(session, room=ctx.room)
            print("[avatar_agent] ✅ Tavus avatar started successfully")
            return True
        except Exception as e:
            print(f"[avatar_agent] ❌ Error starting Tavus avatar: {e}")
            import traceback
            print(f"[avatar_agent] Tavus error traceback: {traceback.format_exc()}")
            return False

    async def start_ai_session():
        try:
            await session.start(
                agent=VideoAssistant(),
                room=ctx.room,
                room_input_options=RoomInputOptions(
                    video_enabled=True,
                ),
            )
            print("[avatar_agent] ✅ AI agent session started with vision enabled")
            return True
        except Exception as e:
            print(f"[avatar_agent] ❌ Error starting AI agent session: {e}")
            import traceback
            print(f"[avatar_agent] Session error traceback: {traceback.format_exc()}")
            return False

    # Run both initialization processes in parallel
    tavus_task = asyncio.create_task(start_tavus_avatar())
    session_task = asyncio.create_task(start_ai_session())
    
    # Wait for both to complete
    tavus_success, session_success = await asyncio.gather(tavus_task, session_task)
    
    if not session_success:
        print("[avatar_agent] ❌ AI session failed to start, exiting")
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