chat_history = {}

def get_history(user_id:str):
    return chat_history.get(user_id,[])

def add_message(user_id: str, role: str, content: str):
    if user_id not in chat_history:
        chat_history[user_id] = []

        chat_history[user_id].append({
            "role":role,
            "content":content,
        })

def clear_history(user_id: str):
    chat_history[user_id] = []