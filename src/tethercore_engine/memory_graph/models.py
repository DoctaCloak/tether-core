from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid

def get_utc_now():
    return datetime.now(timezone.utc)

class EchoBase(BaseModel):
    """
    Base model for an Echo, containing common fields.
    An Echo represents a piece of memory, a thought, a goal, etc.
    """
    content: str = Field(..., description="The textual content of the Echo.")
    tags: Optional[List[str]] = Field(default_factory=list, description="Tags associated with the Echo for categorization and retrieval.")
    user_id: str = Field(..., description="The ID of the user who owns this Echo.")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Arbitrary metadata associated with the Echo.")
    # Optional: Add fields for source (e.g., 'manual', 'agent:focus_mind', 'voice_input')
    # source_application: Optional[str] = None
    # sentiment_score: Optional[float] = None # If sentiment analysis is performed

class EchoCreate(EchoBase):
    """
    Model for creating a new Echo.
    Timestamps will be set automatically if not provided.
    """
    created_at: datetime = Field(default_factory=get_utc_now, description="Timestamp of Echo creation (UTC).")
    updated_at: datetime = Field(default_factory=get_utc_now, description="Timestamp of Echo last update (UTC).")
    # vector: Optional[List[float]] = None # Optional: if vectors are pre-computed and provided

    @validator('created_at', 'updated_at', pre=True, always=True)
    def ensure_timezone_awareness(cls, v):
        if isinstance(v, datetime) and v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v

class Echo(EchoBase):
    """
    Model representing an Echo retrieved from the database, including its ID.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for the Echo (typically assigned by the database).")
    created_at: datetime = Field(description="Timestamp of Echo creation (UTC).")
    updated_at: datetime = Field(description="Timestamp of Echo last update (UTC).")
    # vector: Optional[List[float]] = None # If vectors are stored and retrieved
    # vector_distance: Optional[float] = None # For search results, distance from query vector
    # search_score: Optional[float] = None # For text search results

    class Config:
        from_attributes = True # For Pydantic V2, allows creating from ORM objects or dicts with extra fields

class EchoFilter(BaseModel):
    """
    Model for defining filters when querying for Echos.
    """
    tags_include_any: Optional[List[str]] = None
    tags_include_all: Optional[List[str]] = None
    start_date: Optional[datetime] = None # Filter Echos created after this date
    end_date: Optional[datetime] = None   # Filter Echos created before this date
    user_id: Optional[str] = None
    content_contains: Optional[str] = None
    # Add other filter criteria as needed

# Example usage:
if __name__ == "__main__":
    # Create an Echo
    echo_to_create = EchoCreate(
        content="This is my first thought for TetherCore's memory graph!",
        tags=["project-tether", "idea", "memory-graph"],
        user_id="user_cj_taylor"
    )
    print("Echo to Create:")
    print(echo_to_create.model_dump_json(indent=2))
    print(f"Created at (UTC): {echo_to_create.created_at}")

    # Simulate an Echo retrieved from DB
    retrieved_echo_data = {
        "id": str(uuid.uuid4()),
        "content": "Retrieved thought about AI ethics.",
        "tags": ["ai", "ethics", "important"],
        "user_id": "user_cj_taylor",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "metadata": {"source": "manual_entry", "priority": "high"}
    }
    retrieved_echo = Echo(**retrieved_echo_data)
    print("\nRetrieved Echo:")
    print(retrieved_echo.model_dump_json(indent=2))

    # Filter example
    echo_filter = EchoFilter(
        tags_include_any=["idea", "important"],
        user_id="user_cj_taylor",
        start_date=datetime(2024, 1, 1, tzinfo=timezone.utc)
    )
    print("\nEcho Filter:")
    print(echo_filter.model_dump_json(indent=2))
