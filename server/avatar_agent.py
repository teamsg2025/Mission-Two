import os
import asyncio
import uuid
from dotenv import load_dotenv
from typing import Optional
import json
import logging

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions, RoomOutputOptions
from livekit.plugins import (
    openai,
    google,
    tavus,
    deepgram,
    silero,
    elevenlabs,
)

# Monkey-patch approach: intercept logger.debug() calls directly
_original_livekit_logger_debug = None

def _patched_debug(msg, *args, **kwargs):
    """Intercept debug calls to capture transcript data"""
    # Call original first
    _original_livekit_logger_debug(msg, *args, **kwargs)
    
    # Check if this is a transcript message
    if "received user transcript" in str(msg):
        # kwargs might contain the transcript data in structured logging
        if 'extra' in kwargs and isinstance(kwargs['extra'], dict):
            transcript = kwargs['extra'].get('user_transcript')
            if transcript:
                _global_transcript_history.append(f"User: {transcript}")
                _global_last_transcript[0] = transcript
        
        # Or it might be in args as a dict
        if args and isinstance(args[0], dict):
            transcript = args[0].get('user_transcript')
            if transcript:
                _global_transcript_history.append(f"User: {transcript}")
                _global_last_transcript[0] = transcript

# Import memory service
try:
    from memory_service import get_memory_service
    MEMORY_ENABLED = True
    print("[avatar_agent] ✅ Memory service available")
except Exception as e:
    MEMORY_ENABLED = False
    print(f"[avatar_agent] ⚠️ Memory service not available: {e}")

LANG_EN = "en-US"
LANG_ZH = "cmn-CN"
load_dotenv()

TAVUS_API_KEY = os.getenv("TAVUS_API_KEY")
TAVUS_REPLICA_ID = os.getenv("TAVUS_REPLICA_ID")
TAVUS_PERSONA_ID = os.getenv("TAVUS_PERSONA_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
USER_DISPLAY_NAME = os.getenv("USER_DISPLAY_NAME", "")  # Get display name for memory

# Get language from environment and map to proper constants
LANGUAGE_CODE = os.getenv("LANGUAGE", "en-US")
LANGUAGE = LANG_EN if LANGUAGE_CODE == "en-US" else LANG_ZH

# Global transcript capture storage (shared across sessions in same process)
_global_transcript_history = []
_global_last_transcript = [None]

# Apply monkey-patch at module level (before LiveKit initializes)
_livekit_logger = logging.getLogger("livekit.agents")
_original_livekit_logger_debug = _livekit_logger.debug
_livekit_logger.debug = _patched_debug
print("[avatar_agent] 🐵 Monkey-patched livekit.agents logger.debug()")


class VideoAssistant(Agent):
    def __init__(self, memory_context: str = "", memory_service=None, user_name: str = None, language: str = "en-US") -> None:
        # Store memory service and user_name for runtime use
        self.memory_service = memory_service
        self.user_name = user_name
        self.language = language
        self.conversation_buffer = {"user": None, "assistant": None}
        self.last_user_transcript = ""
        self.last_agent_transcript = ""
        
        # Determine if Chinese or English
        is_chinese = language == "cmn-CN"
        
        # Build instructions with memory context if available
        memory_instructions = ""
        if memory_context:
            memory_instructions = f"""
            
            ---
            
            # IMPORTANT: Previous Conversation Context
            You have had previous study sessions with this user. Here's what you remember:
            
            {memory_context}
            
            **In your FIRST response**, acknowledge that you remember them by mentioning you've studied together before. Be specific if possible (e.g., "Good to see you again! Last time we were looking at algebra together").
            
            Use this context throughout the conversation naturally. Build on previous topics when relevant.
            
            ---
            """
        
        super().__init__(
            instructions = f"""
            You are StudyMate, a real-time, voice-first Study Partner for a student.
            {'你是 StudyMate，一个实时的、以语音为主的学习伙伴。' if is_chinese else ''}
            
            {'🌐 语言: 全程使用中文（普通话）交流。自然、温暖、支持的语气。' if is_chinese else '🌐 Language: Communicate entirely in English. Natural, warm, supportive tone.'}
            
            {memory_instructions}

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

            ### 1. {'认可与共情' if is_chinese else 'Acknowledgement'}
            {'''用同理心接纳用户，不要过度分析。
            - 倾听情绪信号（例如："我跟不上了"）
            - 用一句简短、自然的话反映他们的感受。
            
            示例：
            - "听起来确实很让人沮丧。"
            - "我明白 —— 努力了却感觉卡住了，真的很难受。"
            - "任何人在你的处境都会有同样的感受。"''' if is_chinese else '''Show empathy and acceptance without overanalyzing.  
            - Listen for emotional cues (e.g., "I'm so behind")
            - Reflect what they feel in one short, natural sentence.  
            
            Examples:
            - "That sounds really frustrating."  
            - "I get it — it's hard when you're trying but it feels stuck."  
            - "Anyone in your shoes would feel the same."'''}

            ### 2. {'认知重构' if is_chinese else 'Cognitive Reframe'}
            {'''在认可之后，温和地提供一个新的视角 —— 绝不轻视，始终温柔。
            - 关注 **可控的事情** 和 **已经做对的事情**。
            - 保持简洁和可信。

            示例：
            - "你不是在失败 —— 只是在学习的过程中。"
            - "不是你无法集中注意力 —— 是你的大脑累了。我们一起重新开始吧。"
            - "落后不代表追不上。你已经意识到了，这就是开始。"

            指导原则：
            - 不要说"别担心"或"你没事" —— 用共情 + 重构代替
            - 在重构后提供 *一个* 可行的下一步''' if is_chinese else '''After acknowledging, offer a small shift in perspective — never dismissive, always gentle.
            - Focus on what's **within control** and **what's already done right**.
            - Keep it concise and believable.

            Examples:
            - "You're not failing — you're just in the middle of learning."  
            - "It's not that you can't focus — your brain's just tired. Let's reset together."  
            - "Falling behind doesn't mean you can't catch up. You've already started by noticing it."

            Guidelines:
            - Do not say "don't worry" or "you're fine" - use empathy + reframe instead
            - Offer *one actionable next step* after reframing'''}

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
            - {'如果听不清楚，说："不好意思，能再说一遍吗？"' if is_chinese else 'If unclear audio: "Sorry, could you repeat that?"'}

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
            - {'温暖、尊重的语气，自然的表达（不要太正式）' if is_chinese else 'Casual, friendly, supportive tone'}

            ---

            {'# 示例开场白（中文）' if is_chinese else '# Example openings (English)'}
            {'''- "嗨，又见面了！快速问一下 —— 想专注学习，还是先聊聊天？"
            - If "chat": "没问题。今天过得怎么样，有什么想说的吗？"
            - If "focus": "好的，一步一步来。我们来做个小计划吧。"''' if is_chinese else '''- "Hey, nice to see you again. Quick check — focus on studies, or chat first?"
            - If "chat": "That's fine. Sounds like it's been a day — what's been on your mind?"
            - If "focus": "Alright, one topic at a time. Let's make a quick plan."'''}

            {'现在开始：用一句话温暖地问候用户。保持自然和欢迎的态度。等待用户回应后再继续。' if is_chinese else 'Act now: greet warmly in one sentence. Keep it natural and welcoming. Do nothing else until user responds.'}
            """,
            llm=google.LLM(model="gemini-2.0-flash-exp", temperature=0.8),
            stt=deepgram.STT(
                model="nova-2-general" if is_chinese else "nova-3",  # nova-2 supports Chinese
                language="zh-CN" if is_chinese else "en-US",
            ),
            tts=openai.TTS(voice="nova"),  # Supports both English and Chinese
        )

async def entrypoint(ctx: agents.JobContext):
    room_name = getattr(ctx, 'room', None)
    print(f"[avatar_agent] starting for room={room_name}")
    print(f"[avatar_agent] 🌐 Language: {LANGUAGE_CODE} {'(中文)' if LANGUAGE_CODE == 'cmn-CN' else '(English)'}")
    
    # Check if OpenAI API key is available
    if not OPENAI_API_KEY:
        print("[avatar_agent] WARNING: OPENAI_API_KEY not found in environment variables!")
        print("[avatar_agent] Please set OPENAI_API_KEY in your .env file")
        return 
    else:
        print(f"[avatar_agent] OpenAI API key loaded: {OPENAI_API_KEY[:5]}...")
    
    # Initialize memory service if enabled
    memory_service = None
    user_name = USER_DISPLAY_NAME or None
    
    if MEMORY_ENABLED and user_name:
        try:
            memory_service = get_memory_service()
            print(f"[avatar_agent] 🧠 Memory enabled for user: {user_name}")
        except Exception as e:
            print(f"[avatar_agent] ⚠️ Could not initialize memory service: {e}")
            memory_service = None
    else:
        print(f"[avatar_agent] ⚠️ Memory disabled (MEMORY_ENABLED={MEMORY_ENABLED}, user_name={bool(user_name)})")
    
    await ctx.connect()
    print("[avatar_agent] connected")

    # Retrieve relevant memories for context
    memory_context = ""
    if memory_service and user_name:
        try:
            # Get recent memories for this user
            memories = memory_service.get_all_memories(user_name)
            if memories:
                # Convert to list if needed and get last 10
                if isinstance(memories, list):
                    recent_memories = memories[-10:] if len(memories) > 10 else memories
                else:
                    # If it's a dict or other type, convert to list
                    recent_memories = list(memories)[-10:] if len(list(memories)) > 10 else list(memories)
                
                memory_context = memory_service.format_memories_for_context(recent_memories)
                print(f"[avatar_agent] 📚 Loaded {len(memories)} memories for context")
            else:
                print("[avatar_agent] 📭 No previous memories found")
        except Exception as e:
            print(f"[avatar_agent] ⚠️ Error loading memories: {e}")
            import traceback
            print(f"[avatar_agent] Memory error traceback: {traceback.format_exc()}")
    
    # Create the AI agent session with memory context
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

    # Clear global transcript history for this session
    global _global_transcript_history, _global_last_transcript
    _global_transcript_history.clear()
    _global_last_transcript[0] = None
    print(f"[avatar_agent] 🐵 Using monkey-patched logger for transcript capture")
    
    async def start_ai_session():
        try:
            # Create agent with memory service references
            agent = VideoAssistant(
                memory_context=memory_context,
                memory_service=memory_service,
                user_name=user_name,
                language=LANGUAGE_CODE  # Pass the language from environment
            )
            
            await session.start(
                agent=agent,
                room=ctx.room,
                room_input_options=RoomInputOptions(
                    video_enabled=True,
                ),
            )
            
            print("[avatar_agent] ✅ AI agent session started with monkey-patched transcript capture")
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
        greeting_instruction = "Greet the user warmly in a friendly, welcoming way. Start with 'Hey!' or 'Hi!' in English. "
        if memory_context:
            greeting_instruction += "Remember, you've studied with this user before - acknowledge that naturally! "
        greeting_instruction += "Keep it brief (1-2 sentences). Then wait for their response to detect their language."
        
        await session.generate_reply(
            instructions=greeting_instruction
        )
        print("[avatar_agent] ✅ Initial greeting sent successfully")
        # Mark that conversation session has started (for memory)
        session_had_conversation = True
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
            # Mark that conversation session has started (for memory)
            session_had_conversation = True
        except Exception as e2:
            print(f"[avatar_agent] ❌ Error with fallback greeting: {e2}")
            print(f"[avatar_agent] Fallback error type: {type(e2).__name__}")
            print(f"[avatar_agent] Fallback traceback: {traceback.format_exc()}")

    # Track if conversation happened (for session summary)
    # Note: Gemini Live API is audio-to-audio, so we can't get real-time transcripts
    # We'll just assume conversation happened if the user stayed beyond the greeting
    
    # Monitor for audio events
    async def monitor_audio():
        while True:
            await asyncio.sleep(10)  # Check every 10 seconds
            participants = list(ctx.room.remote_participants.values())
            print(f"[avatar_agent] Room has {len(participants)} participants:")
            for p in participants:
                # RemoteParticipant tracks instead of direct mic/cam attributes
                audio_tracks = [t for t in p.track_publications.values() if t.kind == "audio"]
                video_tracks = [t for t in p.track_publications.values() if t.kind == "video"]
                print(f"  - {p.identity} ({p.name}): audio_tracks={len(audio_tracks)}, video_tracks={len(video_tracks)}")
    
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
    
    # Collect transcripts on disconnect
    if memory_service and user_name:
        @ctx.room.on("participant_disconnected")
        def on_user_left(participant):
            """When user disconnects, summarize conversation and save to memory"""
            if participant.identity != avatar_identity and not participant.identity.startswith("tavus-"):
                print(f"[avatar_agent] 🔄 User left - processing transcript history...")
                print(f"[avatar_agent] 📊 Transcript buffer has {len(_global_transcript_history)} segments")
                
                async def summarize_and_save():
                    if len(_global_transcript_history) > 0:
                        try:
                            # Combine all transcripts
                            full_conversation = "\n".join(_global_transcript_history)
                            print(f"[avatar_agent] 📝 Captured {len(_global_transcript_history)} transcript segments")
                            
                            # Use OpenAI to extract key information
                            import openai
                            client = openai.OpenAI(api_key=OPENAI_API_KEY)
                            
                            summary_response = client.chat.completions.create(
                                model="gpt-4o-mini",
                                messages=[{
                                    "role": "system",
                                    "content": "Extract key information from this study session. Focus on: topics discussed, student concerns, progress made, and action items. Be concise (2-3 sentences max)."
                                }, {
                                    "role": "user",
                                    "content": f"Conversation:\n{full_conversation}"
                                }],
                                max_tokens=150
                            )
                            
                            summary = summary_response.choices[0].message.content
                            print(f"[avatar_agent] 🤖 Generated summary: {summary[:100]}...")
                            
                            # Save to memory
                            import datetime
                            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
                            memory_service.add_conversation_turn(
                                device_id=user_name,
                                user_message=f"Study session on {timestamp}",
                                assistant_message=summary
                            )
                            print(f"[avatar_agent] 💾 Saved conversation summary to memory!")
                            
                        except Exception as e:
                            print(f"[avatar_agent] ⚠️ Error saving transcript summary: {e}")
                            import traceback
                            print(traceback.format_exc())
                    else:
                        # Fallback: If no transcripts captured via summarization, save session with last known info
                        try:
                            import datetime
                            import random
                            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            
                            # Make memory unique by including timestamp and random element
                            session_id = f"session_{int(datetime.datetime.now().timestamp())}"
                            
                            if _global_last_transcript[0]:
                                # Use last thing user said
                                session_note = f"Study session {session_id}: User asked about '{_global_last_transcript[0][:50]}...'. Provided educational support."
                            else:
                                session_note = f"Study session {session_id}: Interactive educational conversation at {timestamp}."
                            
                            memory_service.add_conversation_turn(
                                device_id=user_name,
                                user_message=f"Session at {timestamp}: {_global_last_transcript[0][:100] if _global_last_transcript[0] else 'General study topics'}",
                                assistant_message=session_note
                            )
                            print(f"[avatar_agent] 💾 Saved session marker: '{session_note}'")
                        except Exception as e:
                            print(f"[avatar_agent] ⚠️ Error saving session marker: {e}")
                
                # Run async task
                asyncio.create_task(summarize_and_save())
        
    
    print("[avatar_agent] ✅ Session active - LiveKit will handle lifecycle")
    print(f"[avatar_agent] Memory capture hooks registered for user: {user_name or 'none'}")

# 👇 THIS is what enables:  `python avatar_agent.py dev|start|connect --room demo`
if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))

# you physically run this command: python avatar_agent.py connect --room room-metyln77-lu5x8d
# However, when we try to "automate it", we need to call this file from server.py, meaning it will look for - if __name__ == "__main__":
# parses the room name from the command line and passes it to the entrypoint function.

# python avatar_agent.py connect --room test_room - testing in the terminal