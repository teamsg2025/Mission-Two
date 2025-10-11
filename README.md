# StudyMate AI 🎓

An intelligent, bilingual AI study companion with persistent memory, built with LiveKit real-time video, Tavus visual avatars, and advanced memory systems.

## 🌟 Features

- **Real-time Video Calls with AI Avatar**: Voice and video conversations with a visual AI assistant powered by Tavus
- **Bilingual Support**: Full English and Chinese (Mandarin) support with language-specific optimizations
- **Persistent Memory**: Remembers conversations across sessions using mem0 + Qdrant Cloud
- **Study Coaching**: Evidence-based study techniques (Active Recall, Pomodoro, Interleaving)
- **Emotional Support**: Counseling tools (Acknowledgement, Cognitive Reframing) for student wellbeing
- **Conversation Spark**: AI-generated conversation starters based on user study history to facilitate peer bonding

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│              FRONTEND (React Native + Expo)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  Call Tab    │  │  Spark Tab   │  │ Profile Tab  │         │
│  │ - Language   │  │ - User List  │  │ - Display    │         │
│  │ - Video Call │  │ - Questions  │  │   Name       │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP/WebSocket
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              BACKEND SERVER (FastAPI)                           │
│  ┌──────────────────────────────────────────────────┐          │
│  │  API Endpoints                                   │          │
│  │  • POST /join-room → Generate tokens             │          │
│  │  • GET /api/users → List users                   │          │
│  │  • POST /api/conversation-starters               │          │
│  └──────────────────────────────────────────────────┘          │
│                         │                                        │
│                         │ Spawns subprocess                      │
│                         ▼                                        │
│  ┌──────────────────────────────────────────────────┐          │
│  │  Avatar Agent (LiveKit Process)                  │          │
│  │  • Gemini 2.0 Flash (LLM)                       │          │
│  │  • Deepgram (STT: nova-3 / nova-2)              │          │
│  │  • OpenAI (TTS: "nova" voice)                   │          │
│  │  • Tavus (Visual Avatar)                        │          │
│  │  • Transcript Capture (Monkey-patched logger)   │          │
│  └──────────────────────────────────────────────────┘          │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              MEMORY SYSTEM (mem0 + Qdrant Cloud)                │
│  • User identification via display name                         │
│  • OpenAI embeddings (text-embedding-3-small)                   │
│  • Vector search for relevant memories                          │
│  • GPT-4o-mini for conversation summarization                   │
└─────────────────────────────────────────────────────────────────┘
```

## 🛠️ Tech Stack

### Frontend
- **React Native** with Expo
- **LiveKit React Native SDK** for video/audio
- **TailwindCSS (NativeWind)** for styling
- **AsyncStorage** for local persistence

### Backend
- **FastAPI** (Python) - REST API server
- **LiveKit Agents SDK** - Real-time AI agent framework
- **mem0** - Persistent memory management
- **Qdrant Cloud** - Vector database for embeddings

### AI Services
- **Gemini 2.0 Flash** - LLM for conversation
- **Deepgram** - Speech-to-Text (nova-3 for English, nova-2-general for Chinese)
- **OpenAI** - Text-to-Speech (nova voice), Embeddings, Summarization (GPT-4o-mini)
- **Tavus** - Visual avatar with lip-sync

### Infrastructure
- **LiveKit SFU** - Real-time video infrastructure
- **Qdrant Cloud** - Persistent vector storage

## 📦 Setup

### Prerequisites
- Node.js 18+ and npm
- Python 3.11+
- Expo CLI (`npm install -g expo-cli`)

### Environment Variables

Create `.env` files in both `server/` and root:

**`server/.env`:**
```env
# LiveKit
LIVEKIT_URL=wss://your-livekit-server.livekit.cloud
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret

# Tavus (Visual Avatar)
TAVUS_API_KEY=your_tavus_api_key
TAVUS_REPLICA_ID=your_replica_id
TAVUS_PERSONA_ID=your_persona_id

# AI Services
GOOGLE_API_KEY=your_google_api_key  # Gemini
OPENAI_API_KEY=your_openai_api_key
DEEPGRAM_API_KEY=your_deepgram_api_key

# Memory (Qdrant Cloud)
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your_qdrant_api_key
```

### Installation

**Backend:**
```bash
cd server
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Frontend:**
```bash
cd rn-video-calling-app
npm install
```

## 🚀 Running the Application

### 1. Start Backend Server
```bash
cd server
source venv/bin/activate  # Windows: venv\Scripts\activate
python server.py
# Server runs on http://localhost:3001
```

### 2. Start Frontend
```bash
cd rn-video-calling-app
npx expo start
# Scan QR code with Expo Go app
```

### 3. (Optional) Add Test Users for Conversation Spark
```bash
cd server
python add_test_users.py
# Adds Henry (CS student) and Isaac (Physics student) to Qdrant
```

## 🎯 Key Features Explained

### 1. **Language-Specific AI**
- User selects language before call (English or Chinese)
- Language-specific STT models (Deepgram nova-3 for English, nova-2-general for Chinese)
- Tailored LLM instructions and conversation flow
- Natural multilingual TTS with OpenAI "nova" voice

### 2. **Persistent Memory**
- **Display Name Identification**: Each user has a unique display name stored locally
- **Conversation Capture**: Transcripts captured via monkey-patched LiveKit logger
- **Summarization**: GPT-4o-mini extracts key topics, concerns, and progress on disconnect
- **Vector Storage**: Embeddings stored in Qdrant Cloud for semantic search
- **Context Injection**: Relevant memories loaded into LLM context at session start

### 3. **Conversation Spark**
- Lists all users with study session history
- Generates personalized conversation starter questions using Gemini
- Questions based on target user's actual study topics and concerns
- Facilitates peer-to-peer bonding between students

### 4. **Study Coaching**
The AI agent uses evidence-based techniques:
- **Active Recall**: Testing knowledge before reviewing
- **Pomodoro Technique**: Timed focus sessions with breaks
- **Interleaving**: Connecting related topics across subjects
- **Emotional Support**: Acknowledgement + Cognitive Reframing for student wellbeing

## 📁 Project Structure

```
Mission-Two/
├── rn-video-calling-app/          # React Native frontend
│   ├── app/
│   │   ├── (tabs)/
│   │   │   ├── index.tsx          # Call screen
│   │   │   ├── spark.tsx          # Conversation Spark
│   │   │   └── profile.tsx        # Profile settings
│   │   └── call.tsx               # Video call screen
│   ├── hooks/
│   │   └── useDisplayName.ts      # Persistent user identity
│   └── package.json
│
├── server/                         # Python backend
│   ├── server.py                  # FastAPI server
│   ├── avatar_agent.py            # LiveKit AI agent
│   ├── memory_service.py          # mem0 wrapper
│   ├── add_test_users.py          # Populate test data
│   └── requirements.txt
│
└── README.md
```

## 🔧 Advanced Configuration

### Avatar Agent Process Management
- Each room spawns a separate avatar agent subprocess
- Automatic cleanup of terminated processes via background task
- Manual cleanup endpoint: `POST /cleanup-avatar/{room_name}`
- View active avatars: `GET /active-avatars`

### Memory Management
- Memories indexed by display name (`user_id`)
- Automatic summarization on call disconnect
- Query API: `memory_service.get_all_memories(display_name)`
- Delete API: `memory_service.delete_memories(display_name)`

## 🐛 Debugging

**View backend logs:**
```bash
cd server
python server.py
# Avatar agent logs appear in same console
```

**Check active avatar processes:**
```bash
curl http://localhost:3001/active-avatars
```

**Test Tavus credentials:**
```bash
curl http://localhost:3001/test-tavus
```

## 📝 API Endpoints

### Room Management
- `POST /join-room` - Generate LiveKit token & spawn avatar
- `GET /room-info/{room_name}` - Get room status
- `POST /cleanup-avatar/{room_name}` - Terminate avatar process

### Conversation Spark
- `GET /api/users` - List all users with memories
- `POST /api/conversation-starters` - Generate personalized questions

### Debug
- `GET /active-avatars` - List active avatar processes
- `GET /test-tavus` - Verify Tavus credentials
- `GET /registered-tokens` - View push notification tokens

## 🎓 Study Techniques Implemented

1. **Active Recall**: "Try saying the formula aloud before I show it."
2. **Pomodoro**: "Let's do 20 minutes, then a 3-minute stretch."
3. **Interleaving**: "This pattern also appears in energy equations — let's link them."
4. **Acknowledgement**: "That sounds really frustrating. Anyone in your shoes would feel the same."
5. **Cognitive Reframe**: "You're not failing — you're just in the middle of learning."

## 🌍 Language Support

| Language | STT Model | Code |
|----------|-----------|------|
| English | Deepgram nova-3 | `en-US` |
| Chinese (Mandarin) | Deepgram nova-2-general | `cmn-CN` |

Both languages use the same TTS (OpenAI "nova") and LLM (Gemini 2.0 Flash).

## 📊 Memory System Flow

1. **Call Start**: Load user's recent memories → Inject into LLM context
2. **Conversation**: Transcripts captured via monkey-patched logger
3. **Call End**: Summarize transcripts via GPT-4o-mini → Save to Qdrant
4. **Next Session**: Previous memories loaded automatically

## 🤝 Contributing

This is a production-ready AI study companion. Key areas for enhancement:
- Additional language support
- Group study sessions
- Study analytics dashboard
- Mobile push notifications for peer connections

## 📄 License

MIT License - feel free to use this for your own educational projects!

---

**Built with ❤️ for students worldwide** 🌏
