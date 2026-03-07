"""Service layer for Digest business logic."""

from pathlib import Path
from typing import Sequence

from fastapi import HTTPException

from app.models.digest import Digest
from app.repositories.digest_repository import DigestRepository


class DigestService:
    def __init__(self, repo: DigestRepository):
        self.repo = repo

    async def list_digests(self, limit: int = 30) -> Sequence[Digest]:
        return await self.repo.get_all_ordered(limit=limit)

    async def get_latest(self) -> Digest:
        digest = await self.repo.get_latest()
        if not digest:
            raise HTTPException(status_code=404, detail="No digests found")
        return digest

    async def get_by_uuid(self, digest_id: str) -> Digest:
        digest = await self.repo.get_by_uuid(digest_id)
        if not digest:
            raise HTTPException(status_code=404, detail="Digest not found")
        return digest

    async def get_html_path(self, digest_id: str) -> Path:
        digest = await self.get_by_uuid(digest_id)
        if not digest.html_path:
            raise HTTPException(
                status_code=404, detail="HTML not yet generated for this digest"
            )
        html_path = Path(digest.html_path)
        if not html_path.exists():
            raise HTTPException(status_code=404, detail="HTML file not found on disk")
        return html_path

    async def get_pdf_path(self, digest_id: str) -> Path:
        digest = await self.get_by_uuid(digest_id)
        if not digest.pdf_path:
            raise HTTPException(
                status_code=404, detail="PDF not yet generated for this digest"
            )
        pdf_path = Path(digest.pdf_path)
        if not pdf_path.exists():
            raise HTTPException(status_code=404, detail="PDF file not found on disk")
        return pdf_path
