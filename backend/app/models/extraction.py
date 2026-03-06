"""
Extraction model - Clean text and metadata extracted from a snapshot.

After raw HTML is fetched (snapshot), this stores the cleaned/extracted
text and any structured metadata (title, date, author, etc.).
"""

import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Extraction(Base):
    __tablename__ = "extractions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    snapshot_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("snapshots.id"), nullable=False, unique=True, index=True
    )
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column(
        "metadata", JSON, nullable=True  # title, date, author, etc.
    )
    extraction_method: Mapped[str] = mapped_column(
        String(50), default="trafilatura"  # trafilatura, beautifulsoup, feedparser
    )

    def __repr__(self) -> str:
        text_preview = (self.extracted_text or "")[:50]
        return (
            f"<Extraction(method='{self.extraction_method}', text='{text_preview}...')>"
        )
