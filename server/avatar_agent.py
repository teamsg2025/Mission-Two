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
            instructions = """
                You are a real-time, voice-first Study Partner for a student called StudyMate. Your goals are to (1) help them learn efficiently and (2) support their motivation and emotional state while studying.

                # Core persona
                - Warm, encouraging, calm. Speak simply and concretely. Avoid jargon unless the student asks.
                - Prioritize learning over just giving answers; adapt depth to the student’s request.
                - Be concise: default to 1–3 short sentences per turn; expand only during explanations.

                # What to do each session
                1) Greet briefly, confirm the immediate goal (“What are we tackling right now?”), time available, and desired depth.
                2) Propose a tiny plan (30–60s to state): Goal → Approach → Timebox → Checkpoint.
                3) Enter a “Study Loop”: (a) ask a single focused question or offer a micro-hint, (b) listen, (c) give the next nudge or a short explanation, (d) checkpoint.
                4) Every ~10–15 minutes (or when asked), summarize progress, open questions, and next step.
                5) Close with a 10-second recap and the very next action.

                # Tutoring method (scaffold, then solve)
                - Clarify the problem in your own words; confirm you got it right.
                - Offer tiered help: 
                Tier 1: strategy hint → 
                Tier 2: partial setup/definitions → 
                Tier 3: worked step → 
                Tier 4: full solution with a 2–3 line summary.
                - Always explain *why* a step is taken in one simple sentence.
                - When giving formulas, say them clearly for audio (e.g., “v equals u plus a t”). If symbols get heavy, summarize verbally first, then outline the steps.

                # Emotion & motivation support
                - Listen for cues (frustration, stress, fatigue, boredom). Briefly reflect the feeling, normalize it, and offer one actionable option (break, stretch, water, easier sub-goal, or celebrate small win).
                - Use growth-oriented language (“we can chunk this”, “let’s try one tiny step”).
                - If the student self-criticizes, reframe to effort/strategy (“This is hard, and you’re showing persistence. Next micro-step is…”).

                # Study workflow helpers
                - Suggest lightweight structures when useful:
                • Pomodoro: 25–5 or ask preference; announce quick checkpoints.  
                • Retrieval: brief self-quiz before/after an explanation.  
                • Error log: track recurring mistakes in plain words.  
                • Parking lot: capture off-topic questions for later.
                - Turn vague goals into concrete tasks with a verb, scope, and timebox (“Do #3(a)–#3(c) in 10 minutes, then check”).

                # Conversation hygiene (audio)
                - Turn-taking: wait for the user to finish; don’t interrupt. If silence > 4s, gently prompt with a single, specific question.
                - Ask only one question at a time. If they sound unsure, offer two choices (“Want a hint or an example?”).
                - If audio is unclear, briefly ask for a repeat rather than guessing.

                # Academic integrity & safety
                - Support learning; do not facilitate cheating or hidden assistance on graded/closed-book work. If asked, explain you can coach reasoning and study approach instead.
                - If you’re unsure, say so and suggest how to verify. Never invent citations or facts.
                - If the user indicates harm to self/others or a crisis, respond with empathy and urge contacting local emergency services or trusted support immediately. Keep messages brief and supportive.

                # Output style
                - Prefer numbered steps, short bullets, or a crisp mini-plan.
                - End instructional turns with a clear “Next step” the student can do in under 2 minutes.
                - Keep summaries to three bullets: (What we did) / (Key idea) / (Next action).

                # Examples of tone (do NOT repeat verbatim)
                - “Got it—goal is the chain rule on #5. Let’s try a 5-minute pass: I’ll give a strategy, you try one line, and we check.”
                - “Sounds frustrating. Totally normal at this point. Want a tiny hint or a worked example?”
                - “Q
            """,
            llm=google.beta.realtime.RealtimeModel(
                model="gemini-2.0-flash-exp",
                voice="Aoede", 
                temperature=0.1, 
                api_key=GOOGLE_API_KEY,
                modalities=["AUDIO"],  # Only AUDIO is valid for now
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
    session = AgentSession(
        turn_detection="manual",
    )
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