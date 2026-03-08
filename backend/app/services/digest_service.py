"""
Digest retrieval and file path resolution service.

This module encapsulates business logic for digests (compiled reports):
listing, fetching by ID, and resolving HTML/PDF file paths on disk
with validation that files exist.
"""

from pathlib import Path
from typing import Sequence

from fastapi import HTTPException

from app.models.digest import Digest
from app.repositories.digest_repository import DigestRepository


class DigestService:
    """
    Orchestrates DigestRepository for digest retrieval and path resolution.

    Applies business rules (e.g., file existence checks), raises HTTPExceptions
    for not-found and missing files. All operations are scoped by user_id.
    """

    def __init__(self, repo: DigestRepository):
        self.repo = repo

    async def list_digests(self, user_id: int, limit: int = 30) -> Sequence[Digest]:
        """List digests for a user, most recent first, limited by count."""
        return await self.repo.get_all_ordered(user_id, limit=limit)

    async def get_latest(self, user_id: int) -> Digest:
        """
        Fetch the most recent digest for a user.

        Raises:
            HTTPException 404: No digests found.
        """
        digest = await self.repo.get_latest(user_id)
        if not digest:
            raise HTTPException(status_code=404, detail="No digests found")
        return digest

    async def get_by_uuid(self, digest_id: str, user_id: int) -> Digest:
        digest = await self.repo.get_by_uuid(digest_id, user_id=user_id)
        if not digest:
            raise HTTPException(status_code=404, detail="Digest not found")
        return digest

    async def get_html_path(self, digest_id: str, user_id: int) -> Path:
        """
        Resolve the HTML file path for a digest. Validates file exists on disk.

        Raises:
            HTTPException 404: Digest not found, HTML not yet generated, or file missing.
        """
        digest = await self.get_by_uuid(digest_id, user_id)
        if not digest.html_path:
            raise HTTPException(
                status_code=404, detail="HTML not yet generated for this digest"
            )
        html_path = Path(digest.html_path)
        if not html_path.exists():
            raise HTTPException(status_code=404, detail="HTML file not found on disk")
        return html_path

    async def get_pdf_path(self, digest_id: str, user_id: int) -> Path:
        """
        Resolve the PDF file path for a digest. Validates file exists on disk.

        Raises:
            HTTPException 404: Digest not found, PDF not yet generated, or file missing.
        """
        digest = await self.get_by_uuid(digest_id, user_id)
        if not digest.pdf_path:
            raise HTTPException(
                status_code=404, detail="PDF not yet generated for this digest"
            )
        pdf_path = Path(digest.pdf_path)
        if not pdf_path.exists():
            raise HTTPException(status_code=404, detail="PDF file not found on disk")
        return pdf_path
