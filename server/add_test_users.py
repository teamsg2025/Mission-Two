"""
Script to add test users with memories to Qdrant Cloud for testing Conversation Spark
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
    
    user1_memories = [
        ("Learning data structures", "Discussed linked lists, stacks, and queues. Covered implementation details and time complexity. Student working on a project using these structures."),
        ("Algorithm complexity review", "Reviewed Big O notation - O(n), O(log n), O(n²). Student asked about analyzing recursive algorithms and optimizing code."),
        ("Struggling with recursion", "Student felt confused about recursive functions. Explained with examples like factorial and Fibonacci. Student understood better after tracing execution step by step."),
        ("Binary search trees", "Worked through BST operations - insertion, deletion, search. Student is preparing for a data structures exam next week."),
        ("Database design questions", "Discussed normalization, SQL joins, and indexing. Student mentioned they have a database project due soon and needs help with schema design."),
    ]
    
    for user_msg, assistant_msg in user1_memories:
        memory_service.add_conversation_turn(
            device_id=user1_name,
            user_message=user_msg,
            assistant_message=assistant_msg
        )
        print(f"  ✅ Added memory: {user_msg[:50]}...")
    
    # Test User 2: Physics student
    user2_name = "Isaac"
    print(f"\n👤 Adding Test User 2: {user2_name}")
    
    user2_memories = [
        ("Newton's laws of motion", "Student working on force, mass, and acceleration problems. Discussed F=ma and free body diagrams. Struggling with tension and friction problems."),
        ("Kinematics equations", "Practiced projectile motion and velocity calculations. Student has trouble visualizing parabolic trajectories and choosing the right equations."),
        ("Electromagnetism concepts", "Reviewed electric fields, magnetic fields, and Maxwell's equations. Student is preparing for a test on electromagnetic induction and feels nervous."),
        ("Thermodynamics and entropy", "Discussed heat transfer, first and second laws of thermodynamics. Student mentioned they have a lab report on heat engines due soon."),
        ("Feeling overwhelmed with physics", "Student expressed anxiety about upcoming exams. Talked about breaking study sessions into smaller chunks and practicing more problem sets."),
        ("Quantum mechanics intro", "Worked through wave-particle duality, uncertainty principle, and Schrödinger equation basics. Student found it abstract but made good progress."),
    ]
    
    for user_msg, assistant_msg in user2_memories:
        memory_service.add_conversation_turn(
            device_id=user2_name,
            user_message=user_msg,
            assistant_message=assistant_msg
        )
        print(f"  ✅ Added memory: {user_msg[:50]}...")
    
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

