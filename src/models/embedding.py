from datetime import datetime
from pgvector.sqlalchemy import Vector
from sqlalchemy import Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base

class EventEmbedding (Base):
    """vector embbeding for a WW2 Event"""
    __tablename__ = "event_embeddings"

    id: Mapped[int] = mapped_column(primary_key= True)
    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"), nullable=False, unique=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding = mapped_column(Vector(768), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    #Relationship
    event = relationship("Event")

    