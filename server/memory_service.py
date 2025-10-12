"""
Memory Service using mem0 Platform API for persistent conversation memory.
User display name-based tracking for StudyMate AI assistant.
"""
import os
from typing import List, Dict, Optional
from datetime import datetime
from mem0 import MemoryClient

class MemoryService:
    """
    Manages conversation memory using mem0 Platform API with user display name identification.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Memory Service with mem0 Platform API.
        
        Args:
            api_key: mem0 API key (falls back to MEM0_API_KEY env var)
        """
        mem0_api_key = api_key or os.getenv("MEM0_API_KEY")
        
        if not mem0_api_key:
            raise ValueError("MEM0_API_KEY is required for mem0 Platform API")
        
        # Optional: Get organization and project IDs
        org_id = os.getenv("MEM0_ORG_ID")
        project_id = os.getenv("MEM0_PROJECT_ID")
        
        try:
            # Initialize mem0 Platform client with optional org/project
            client_params = {"api_key": mem0_api_key}
            
            if org_id:
                client_params["org_id"] = org_id
                print(f"[MemoryService] 🏢 Using organization: {org_id}")
            
            if project_id:
                client_params["project_id"] = project_id
                print(f"[MemoryService] 📁 Using project: {project_id}")
            
            self.client = MemoryClient(**client_params)
            
            print(f"[MemoryService] ✅ Initialized with mem0 Platform API")
            print(f"[MemoryService] 🌐 Using managed cloud infrastructure")
            print(f"[MemoryService] 💾 Persistent cross-session memory enabled!")
            print(f"[MemoryService] 📊 Access dashboard at: https://app.mem0.ai")
            
        except Exception as e:
            print(f"[MemoryService] ❌ Error initializing mem0 Platform client: {e}")
            import traceback
            print(f"[MemoryService] Traceback: {traceback.format_exc()}")
            raise
    
    def get_relevant_memories(self, user_id: str, query: str, limit: int = 5) -> List[Dict]:
        """
        Retrieve relevant memories for a user based on current query.
        
        Args:
            user_id: User display name
            query: Current conversation context or user message
            limit: Maximum number of memories to retrieve
            
        Returns:
            List of relevant memory dictionaries
        """
        try:
            # Search for relevant memories using Platform API
            results = self.client.search(
                query=query,
                user_id=user_id,
                limit=limit
            )
            
            print(f"[MemoryService] 🔍 Retrieved {len(results)} memories for user: {user_id}")
            return results
            
        except Exception as e:
            print(f"[MemoryService] ❌ Error retrieving memories: {e}")
            return []
    
    def add_memory(self, user_id: str, message: str, role: str = "user") -> bool:
        """
        Add a new memory from the conversation.
        
        Args:
            user_id: User display name
            message: The message content to remember
            role: Role of the speaker (user or assistant)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Add memory with metadata using Platform API
            self.client.add(
                messages=[{
                    "role": role,
                    "content": message
                }],
                user_id=user_id,
                metadata={
                    "timestamp": datetime.now().isoformat(),
                    "role": role
                }
            )
            
            print(f"[MemoryService] 💾 Added {role} memory for user: {user_id}")
            return True
            
        except Exception as e:
            print(f"[MemoryService] ❌ Error adding memory: {e}")
            return False
    
    def add_conversation_turn(self, user_id: str, user_message: str, assistant_message: str) -> bool:
        """
        Add a complete conversation turn (user + assistant).
        
        Args:
            user_id: User display name
            user_message: User's message
            assistant_message: Assistant's response
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Add both messages in sequence using Platform API
            self.client.add(
                messages=[
                    {"role": "user", "content": user_message},
                    {"role": "assistant", "content": assistant_message}
                ],
                user_id=user_id,
                metadata={
                    "timestamp": datetime.now().isoformat(),
                    "type": "conversation_turn"
                }
            )
            
            print(f"[MemoryService] 💾 Added conversation turn for user: {user_id}")
            return True
            
        except Exception as e:
            print(f"[MemoryService] ❌ Error adding conversation turn: {e}")
            return False
    
    def get_all_memories(self, user_id: str) -> List[Dict]:
        """
        Get all memories for a specific user.
        
        Args:
            user_id: User display name
            
        Returns:
            List of all memories
        """
        try:
            # Platform API returns list directly
            results = self.client.get_all(user_id=user_id)
            
            # Handle both list and dict response formats
            if isinstance(results, dict) and 'results' in results:
                memories = results['results']
                print(f"[MemoryService] 📚 Retrieved {len(memories)} memories for user: {user_id}")
                return memories
            
            print(f"[MemoryService] 📚 Retrieved {len(results)} memories for user: {user_id}")
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
    
    def get_all_users(self) -> Dict:
        """
        Get all users, agents, and runs that have memories in mem0 Platform.
        Uses the REST API directly for more reliable results.
        
        Returns:
            Dictionary with 'users', 'agents', and 'runs' lists
        """
        try:
            # Use REST API directly (more reliable than SDK's users() method)
            import requests
            
            api_key = os.getenv("MEM0_API_KEY")
            url = "https://api.mem0.ai/v1/entities/"
            headers = {"Authorization": f"Token {api_key}"}
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract entities by type from results
            results = data.get("results", [])
            
            users = [entity["name"] for entity in results if entity.get("type") == "user"]
            agents = [entity["name"] for entity in results if entity.get("type") == "agent"]
            runs = [entity["name"] for entity in results if entity.get("type") == "run"]
            
            print(f"[MemoryService] 👥 Retrieved {len(users)} users, {len(agents)} agents, {len(runs)} runs")
            
            return {
                "users": users,
                "agents": agents,
                "runs": runs
            }
            
        except Exception as e:
            print(f"[MemoryService] ❌ Error getting all users: {e}")
            import traceback
            print(f"[MemoryService] Traceback: {traceback.format_exc()}")
            return {"users": [], "agents": [], "runs": []}
    
    def delete_memories(self, user_id: str) -> bool:
        """
        Delete all memories for a user (use with caution).
        
        Args:
            user_id: User display name
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.delete_all(user_id=user_id)
            print(f"[MemoryService] 🗑️ Deleted all memories for user: {user_id}")
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

