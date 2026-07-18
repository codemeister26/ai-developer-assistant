chat_history = {}

MAX_HISTORY = 10            # sirf last 10 messages rakhte hain ✅

def get_history(conversation_id: str):
    return chat_history.get(conversation_id, [])

def add_message(conversation_id: str, role: str, content: str):
    if conversation_id not in chat_history:
        chat_history[conversation_id] = []

    chat_history[conversation_id].append({"role": role, "content": content})

    # Memory limit — purani history trim karo
    if len(chat_history[conversation_id]) > MAX_HISTORY:
        chat_history[conversation_id] = chat_history[conversation_id][-MAX_HISTORY:]

def clear_history(conversation_id: str):
    chat_history[conversation_id] = []