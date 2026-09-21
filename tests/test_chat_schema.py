import uuid

import pytest
from pydantic import ValidationError

from app.config.settings import MAX_MESSAGE_LENGTH
from app.schemas.chat import ChatRequest


def test_valid_request_accepted():
    conversation_id = str(uuid.uuid4())
    request = ChatRequest(message="hello", conversation_id=conversation_id)

    assert request.message == "hello"
    assert request.conversation_id == conversation_id


def test_conversation_id_optional():
    assert ChatRequest(message="hello").conversation_id is None


def test_message_whitespace_stripped():
    assert ChatRequest(message="  hello  ").message == "hello"


@pytest.mark.parametrize("blank", ["", "   ", "\n\t "])
def test_blank_message_rejected(blank):
    """Khaali message LLM call waste karta tha — ab reject hota hai"""
    with pytest.raises(ValidationError, match="message cannot be empty"):
        ChatRequest(message=blank)


def test_message_at_max_length_accepted():
    assert len(ChatRequest(message="a" * MAX_MESSAGE_LENGTH).message) == MAX_MESSAGE_LENGTH


def test_message_over_max_length_rejected():
    with pytest.raises(ValidationError):
        ChatRequest(message="a" * (MAX_MESSAGE_LENGTH + 1))


def test_non_uuid_conversation_id_rejected():
    """Junk ID se fake conversations ban jaati thi"""
    with pytest.raises(ValidationError, match="conversation_id must be a valid UUID"):
        ChatRequest(message="hello", conversation_id="not-a-uuid")
