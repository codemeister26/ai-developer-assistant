from sqlalchemy.orm import Session
from app.db.models import Conversation, Message

def create_conversation(db: Session, conversation_id:str):
    # to save new convo in data base
    conversation = Conversation(id = conversation_id)
    db.add(conversation)
    db.commit()
    return conversation

def get_conversation(db: Session, conversation_id: str):
    """Check karo ki conversation exist karti hai ya nahi"""
    return db.query(Conversation).filter(Conversation.id == conversation_id).first()

def get_All_Conversation(db:Session):
    # check for all convo
    return db.query(Conversation).all()

def add_message(db:Session, conversation_id:str, role:str, content:str):
     """Ek message conversation mein save karo"""
     message = Message(
         conversation_id=conversation_id,
         role=role,
         content=content
     )
     db.add(message)
     db.commit()
     return message

def get_messages(db:Session, conversation_id:str, limit:int=10):
    """Conversation ki last N messages do — context ke liye"""
    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.id.desc())
        .limit(limit)
        .all()
    )
    return list(reversed(messages))

def delete_conversation(db: Session, conversation_id: str) -> bool:
    """Conversation aur uske saare messages delete karo. Returns True agar conversation exist karti thi"""
    db.query(Message).filter(Message.conversation_id == conversation_id).delete()
    deleted_count = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id)
        .delete()
    )
    db.commit()
    return deleted_count > 0

