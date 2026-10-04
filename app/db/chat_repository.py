from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session
from app.config.settings import CONVERSATION_PAGE_SIZE, HISTORY_MESSAGE_LIMIT
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

def get_all_conversations(
    db: Session,
    search: str | None = None,
    limit: int = CONVERSATION_PAGE_SIZE,
    offset: int = 0,
):
    """Conversations list — pinned pehle, phir newest.

    Title user ka diya hua naam hai; na ho toh pehla user message. Subquery se
    aata hai, isliye har conversation ke liye alag query nahi chalti, aur ye
    conversation_id wale index ko use karti hai.

    search diya ho toh title aur message content dono mein dhoondha jaata hai.
    """
    first_user_message = (
        select(Message.content)
        .where(Message.conversation_id == Conversation.id, Message.role == "user")
        .order_by(Message.id)
        .limit(1)
        .correlate(Conversation)
        .scalar_subquery()
    )

    # User ka rename kiya hua naam jeetta hai, warna pehla message
    title = func.coalesce(Conversation.title, first_user_message).label("title")

    query = db.query(
        Conversation.id,
        Conversation.created_at,
        Conversation.pinned,
        title,
    )

    if search:
        pattern = f"%{search}%"
        # Kisi bhi message mein match mile toh wo conversation bhi chahiye —
        # sirf title match kaafi nahi hoga
        matching_message = (
            select(Message.id)
            .where(
                Message.conversation_id == Conversation.id,
                Message.content.ilike(pattern),
            )
            .limit(1)
            .correlate(Conversation)
            .exists()
        )
        query = query.filter(
            or_(Conversation.title.ilike(pattern), matching_message)
        )

    return (
        query
        .order_by(Conversation.pinned.desc(), Conversation.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )

def rename_conversation(db: Session, conversation_id: str, title: str | None) -> bool:
    """Custom naam set karo. title None ho toh auto-title par wapas chala jaata hai."""
    conversation = get_conversation(db, conversation_id)

    if conversation is None:
        return False

    conversation.title = title
    db.commit()
    return True

def set_pinned(db: Session, conversation_id: str, pinned: bool) -> bool:
    conversation = get_conversation(db, conversation_id)

    if conversation is None:
        return False

    conversation.pinned = pinned
    db.commit()
    return True

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

def get_messages(db:Session, conversation_id:str, limit:int=HISTORY_MESSAGE_LIMIT):
    """Conversation ki last N messages do — context ke liye"""
    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.id.desc())
        .limit(limit)
        .all()
    )
    return list(reversed(messages))

def delete_messages_from(db: Session, conversation_id: str, message_id: int) -> int:
    """Is message ko aur uske baad ke sabko hatao. Returns kitne delete hue.

    Edit-and-resend ke liye: purana sawaal aur uske baad ka sab jaata hai, phir
    naya sawaal add hota hai.
    """
    deleted = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id, Message.id >= message_id)
        .delete()
    )
    db.commit()
    return deleted

def delete_trailing_assistant_message(db: Session, conversation_id: str) -> bool:
    """Aakhri message agar assistant ka hai toh hatao — regenerate ke liye"""
    last = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.id.desc())
        .first()
    )

    if last is None or last.role != "assistant":
        return False

    db.delete(last)
    db.commit()
    return True

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

