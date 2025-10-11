"""
Memory Service using mem0 for persistent conversation memory.
Device-based user tracking for StudyMate AI assistant.
"""
import os
from typing import List, Dict, Optional
from datetime import datetime
from mem0 import Memory

class MemoryService:
    """
    Manages conversation memory using mem0 with device-based user identification.
    """
    
    def __init__(self, openai_api_key: Optional[str] = None):
        """
        Initialize Memory Service with OpenAI for embeddings.
        
        Args:
            openai_api_key: OpenAI API key for embeddings (falls back to env var)
        """
        api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required for mem0 embeddings")
        
        # Configure mem0 with OpenAI embeddings
        # Use in-memory Qdrant to avoid file locking issues with concurrent avatar subprocesses
        
        config = {
            "llm": {
                "provider": "openai",
                "config": {
                    "model": "gpt-4o-mini",
                    "temperature": 0.1,
                    "api_key": api_key
                }
            },
            "embedder": {
                "provider": "openai",
                "config": {
                    "model": "text-embedding-3-small",
                    "api_key": api_key
                }
            },
            "vector_store": {
                "provider": "qdrant",
                "config": {
                    "collection_name": "studymate_memories",
                    "url": os.getenv("QDRANT_URL"),
                    "api_key": os.getenv("QDRANT_API_KEY"),
                }
            },
            "version": "v1.1"
        }
        
        try:
            self.memory = Memory.from_config(config)
            qdrant_url = os.getenv("QDRANT_URL", "not-set")
            if qdrant_url and qdrant_url != "not-set":
                print(f"[MemoryService] ✅ Initialized with Qdrant Cloud")
                print(f"[MemoryService] 🌐 Connected to: {qdrant_url[:50]}...")
                print(f"[MemoryService] 💾 Persistent cross-session memory enabled!")
            else:
                print(f"[MemoryService] ✅ Initialized (no Qdrant URL - using default)")
        except Exception as e:
            print(f"[MemoryService] ❌ Error initializing memory: {e}")
            # Try to provide more context
            import traceback
            print(f"[MemoryService] Traceback: {traceback.format_exc()}")
            raise
    
    def get_relevant_memories(self, device_id: str, query: str, limit: int = 5) -> List[Dict]:
        """
        Retrieve relevant memories for a device/user based on current query.
        
        Args:
            device_id: Unique device identifier
            query: Current conversation context or user message
            limit: Maximum number of memories to retrieve
            
        Returns:
            List of relevant memory dictionaries
        """
        try:
            # Search for relevant memories
            results = self.memory.search(
                query=query,
                user_id=device_id,
                limit=limit
            )
            
            print(f"[MemoryService] 🔍 Retrieved {len(results)} memories for device: {device_id[:8]}...")
            return results
            
        except Exception as e:
            print(f"[MemoryService] ❌ Error retrieving memories: {e}")
            return []
    
    def add_memory(self, device_id: str, message: str, role: str = "user") -> bool:
        """
        Add a new memory from the conversation.
        
        Args:
            device_id: Unique device identifier
            message: The message content to remember
            role: Role of the speaker (user or assistant)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Add memory with metadata
            self.memory.add(
                messages=[{
                    "role": role,
                    "content": message
                }],
                user_id=device_id,
                metadata={
                    "timestamp": datetime.now().isoformat(),
                    "role": role
                }
            )
            
            print(f"[MemoryService] 💾 Added {role} memory for device: {device_id[:8]}...")
            return True
            
        except Exception as e:
            print(f"[MemoryService] ❌ Error adding memory: {e}")
            return False
    
    def add_conversation_turn(self, device_id: str, user_message: str, assistant_message: str) -> bool:
        """
        Add a complete conversation turn (user + assistant).
        
        Args:
            device_id: Unique device identifier
            user_message: User's message
            assistant_message: Assistant's response
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Add both messages in sequence
            self.memory.add(
                messages=[
                    {"role": "user", "content": user_message},
                    {"role": "assistant", "content": assistant_message}
                ],
                user_id=device_id,
                metadata={
                    "timestamp": datetime.now().isoformat(),
                    "type": "conversation_turn"
                }
            )
            
            print(f"[MemoryService] 💾 Added conversation turn for device: {device_id[:8]}...")
            return True
            
        except Exception as e:
            print(f"[MemoryService] ❌ Error adding conversation turn: {e}")
            return False
    
    def get_all_memories(self, device_id: str) -> List[Dict]:
        """
        Get all memories for a specific device/user.
        
        Args:
            device_id: Unique device identifier
            
        Returns:
            List of all memories
        """
        try:
            results = self.memory.get_all(user_id=device_id)
            
            # mem0 returns dict with 'results' key containing the array
            if isinstance(results, dict) and 'results' in results:
                memories = results['results']
                print(f"[MemoryService] 📚 Retrieved {len(memories)} memories for device: {device_id[:8]}...")
                return memories
            
            print(f"[MemoryService] 📚 Retrieved {len(results)} memories for device: {device_id[:8]}...")
            return results
            
        except Exception as e:
            print(f"[MemoryService] ❌ Error getting all memories: {e}")
            import traceback
            print(f"[MemoryService] Traceback: {traceback.format_exc()}")
            return []
    
    def format_memories_for_context(self, memories: List[Dict]) -> str:
        """
        Format memories into a context string for the LLM.
        
        Args:
            memories: List of memory dictionaries
            
        Returns:
            Formatted string for LLM context
        """
        if not memories:
            return ""
        
        context_parts = ["# Previous Conversation Memories"]
        
        for i, memory in enumerate(memories, 1):
            # mem0 memories are dicts with 'memory' key
            if isinstance(memory, dict):
                content = memory.get('memory', str(memory))
                context_parts.append(f"{i}. {content}")
            else:
                context_parts.append(f"{i}. {str(memory)}")
        
        return "\n".join(context_parts)
    
    def delete_memories(self, device_id: str) -> bool:
        """
        Delete all memories for a device/user (use with caution).
        
        Args:
            device_id: Unique device identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.memory.delete_all(user_id=device_id)
            print(f"[MemoryService] 🗑️ Deleted all memories for device: {device_id[:8]}...")
            return True
            
        except Exception as e:
            print(f"[MemoryService] ❌ Error deleting memories: {e}")
            return False


# Singleton instance
_memory_service_instance = None

def get_memory_service() -> MemoryService:
    """
    Get or create the singleton MemoryService instance.
    
    Returns:
        MemoryService instance
    """
    global _memory_service_instance
    
    if _memory_service_instance is None:
        try:
            _memory_service_instance = MemoryService()
            print("[MemoryService] 🎯 Singleton instance created")
        except Exception as e:
            print(f"[MemoryService] ❌ Failed to create singleton: {e}")
            raise
    
    return _memory_service_instance

