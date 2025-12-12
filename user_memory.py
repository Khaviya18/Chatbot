"""
User Memory System - Stores and manages user information, preferences, and conversation history
Similar to Snapchat's My AI personality system
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Optional

MEMORY_DIR = "./user_memory"
MEMORY_FILE = os.path.join(MEMORY_DIR, "user_memory.json")
CONVERSATION_FILE = os.path.join(MEMORY_DIR, "conversation_history.json")

# Ensure memory directory exists
os.makedirs(MEMORY_DIR, exist_ok=True)

def load_memory() -> Dict:
    """Load user memory from file"""
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {
        "user_info": {},
        "preferences": {},
        "interests": [],
        "important_facts": [],
        "conversation_topics": [],
        "personality_traits": {},
        "last_updated": None
    }

def save_memory(memory: Dict):
    """Save user memory to file"""
    memory["last_updated"] = datetime.now().isoformat()
    with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(memory, f, indent=2, ensure_ascii=False)

def load_conversation_history() -> List[Dict]:
    """Load conversation history"""
    if os.path.exists(CONVERSATION_FILE):
        try:
            with open(CONVERSATION_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return []

def save_conversation_history(history: List[Dict], max_entries: int = 50):
    """Save conversation history (keep last N entries)"""
    # Keep only the most recent entries
    history = history[-max_entries:]
    with open(CONVERSATION_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

def add_to_conversation(user_message: str, assistant_message: str):
    """Add a conversation turn to history"""
    history = load_conversation_history()
    history.append({
        "timestamp": datetime.now().isoformat(),
        "user": user_message,
        "assistant": assistant_message
    })
    save_conversation_history(history)

def get_recent_conversation_context(max_turns: int = 10) -> str:
    """Get recent conversation context for continuity"""
    history = load_conversation_history()
    recent = history[-max_turns:] if len(history) > max_turns else history
    
    context = ""
    for turn in recent:
        context += f"User: {turn['user']}\nAssistant: {turn['assistant']}\n\n"
    
    return context

def format_memory_for_prompt(memory: Dict) -> str:
    """Format user memory into a prompt-friendly string"""
    if not memory.get("user_info") and not memory.get("important_facts"):
        return "No previous information about the user."
    
    info = []
    
    if memory.get("user_info"):
        info.append("USER INFORMATION:")
        for key, value in memory["user_info"].items():
            info.append(f"- {key}: {value}")
    
    if memory.get("important_facts"):
        info.append("\nIMPORTANT FACTS ABOUT USER:")
        for fact in memory["important_facts"]:
            info.append(f"- {fact}")
    
    if memory.get("preferences"):
        info.append("\nUSER PREFERENCES:")
        for key, value in memory["preferences"].items():
            info.append(f"- {key}: {value}")
    
    if memory.get("interests"):
        info.append(f"\nUSER INTERESTS: {', '.join(memory['interests'])}")
    
    return "\n".join(info)

def extract_user_info_from_conversation(user_message: str, assistant_message: str, memory: Dict) -> Dict:
    """
    Extract important user information from conversation
    This is a simple extraction - in production, you'd use NLP/ML models
    """
    updated = False
    message_lower = user_message.lower()
    
    # Extract name patterns
    if "my name is" in message_lower or "i'm" in message_lower or "i am" in message_lower:
        # Simple name extraction (can be improved)
        words = user_message.split()
        for i, word in enumerate(words):
            if word.lower() in ["name", "i'm", "i", "am", "called"]:
                if i + 1 < len(words):
                    name = words[i + 1].strip(".,!?")
                    if name and len(name) > 1:
                        memory["user_info"]["name"] = name
                        updated = True
                        break
    
    # Extract location
    location_keywords = ["live in", "from", "located in", "based in"]
    for keyword in location_keywords:
        if keyword in message_lower:
            parts = user_message.lower().split(keyword)
            if len(parts) > 1:
                location = parts[1].split(".")[0].split(",")[0].strip()
                if location:
                    memory["user_info"]["location"] = location
                    updated = True
                    break
    
    # Extract interests/hobbies
    interest_keywords = ["like", "love", "enjoy", "interested in", "hobby", "passion"]
    for keyword in interest_keywords:
        if keyword in message_lower:
            # Extract the thing they like
            parts = user_message.lower().split(keyword)
            if len(parts) > 1:
                interest = parts[1].split(".")[0].split(",")[0].strip()
                if interest and interest not in memory.get("interests", []):
                    if "interests" not in memory:
                        memory["interests"] = []
                    memory["interests"].append(interest)
                    updated = True
    
    return memory if updated else None



