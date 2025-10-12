"""
Script to add test users with memories to mem0 Platform for testing Conversation Spark
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Add server directory to path
sys.path.insert(0, os.path.dirname(__file__))

from memory_service import get_memory_service

def add_test_users():
    """Add 2 test users with realistic study memories"""
    
    print("🔧 Initializing memory service...")
    memory_service = get_memory_service()
    
    # Test User 1: CS student
    user1_name = "Henry"
    print(f"\n👤 Adding Test User 1: {user1_name}")
    
    # Note: mem0 only interprets user messages, so put all info in user_message
    user1_memories = [
        "Learning data structures: discussed linked lists, stacks, and queues. Covered implementation details and time complexity. Working on a project using these structures.",
        "Algorithm complexity review: reviewed Big O notation - O(n), O(log n), O(n²). Asked about analyzing recursive algorithms and optimizing code.",
        "Struggling with recursion: felt confused about recursive functions. Learned with examples like factorial and Fibonacci. Understood better after tracing execution step by step.",
        "Binary search trees: worked through BST operations - insertion, deletion, search. Preparing for a data structures exam next week.",
        "Database design: discussed normalization, SQL joins, and indexing. Have a database project due soon and need help with schema design.",
    ]
    
    for memory in user1_memories:
        memory_service.add_conversation_turn(
            user_id=user1_name,
            user_message=memory,
            assistant_message=""  # Empty as mem0 only interprets user messages
        )
        print(f"  ✅ Added memory: {memory[:50]}...")
    
    # Test User 2: Physics student
    user2_name = "Isaac"
    print(f"\n👤 Adding Test User 2: {user2_name}")
    
    user2_memories = [
        "Newton's laws of motion: working on force, mass, and acceleration problems. Learning F=ma and free body diagrams. Struggling with tension and friction problems.",
        "Kinematics equations: practiced projectile motion and velocity calculations. Have trouble visualizing parabolic trajectories and choosing the right equations.",
        "Electromagnetism concepts: reviewed electric fields, magnetic fields, and Maxwell's equations. Preparing for a test on electromagnetic induction and feeling nervous about it.",
        "Thermodynamics and entropy: discussed heat transfer, first and second laws of thermodynamics. Have a lab report on heat engines due soon.",
        "Feeling overwhelmed with physics: expressed anxiety about upcoming exams. Learning to break study sessions into smaller chunks and practice more problem sets.",
        "Quantum mechanics intro: worked through wave-particle duality, uncertainty principle, and Schrödinger equation basics. Found it abstract but made good progress.",
    ]
    
    for memory in user2_memories:
        memory_service.add_conversation_turn(
            user_id=user2_name,
            user_message=memory,
            assistant_message=""  # Empty as mem0 only interprets user messages
        )
        print(f"  ✅ Added memory: {memory[:50]}...")
    
    # Verify memories were added
    print("\n🔍 Verifying memories...")
    user1_memories_retrieved = memory_service.get_all_memories(user1_name)
    user2_memories_retrieved = memory_service.get_all_memories(user2_name)
    
    print(f"\n✅ Test User 1 ({user1_name}): {len(user1_memories_retrieved)} memories")
    print(f"✅ Test User 2 ({user2_name}): {len(user2_memories_retrieved)} memories")
    
    print("\n🎉 Test users added successfully!")
    print(f"\nYou can now test Conversation Spark with:")
    print(f"  - User 1 (CS): {user1_name}")
    print(f"  - User 2 (Physics): {user2_name}")

if __name__ == "__main__":
    try:
        add_test_users()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        print(traceback.format_exc())
        sys.exit(1)

