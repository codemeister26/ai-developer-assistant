chat_history = {}

MAX_HISTORY = 10            # sirf last 10 messages rakhte hain ✅

def get_history(user_id: str):
    return chat_history.get(user_id, [])

def add_message(user_id: str, role: str, content: str):
    if user_id not in chat_history:
        chat_history[user_id] = []

    chat_history[user_id].append({"role": role, "content": content})

    # Memory limit — purani history trim karo
    if len(chat_history[user_id]) > MAX_HISTORY:
        chat_history[user_id] = chat_history[user_id][-MAX_HISTORY:]

def clear_history(user_id: str):
    chat_history[user_id] = []