"""Service layer for orchestrator configuration."""

import json
from typing import Optional

from fastapi import HTTPException

from app.repositories.orchestrator_config_repository import OrchestratorConfigRepository
from app.schemas.orchestrator_config import (
    OrchestratorConfigResponse,
    OrchestratorConfigSchema,
)


class OrchestratorConfigService:
    def __init__(self, repo: OrchestratorConfigRepository):
        self.repo = repo

    async def get_config(self) -> OrchestratorConfigResponse:
        """Return the current config with defaults filled in."""
        row = await self.repo.get()
        if row and row.config:
            schema = OrchestratorConfigSchema.model_validate(row.config)
            return OrchestratorConfigResponse(
                config=schema, updated_at=row.updated_at
            )
        return OrchestratorConfigResponse(
            config=OrchestratorConfigSchema(), updated_at=None
        )

    async def get_config_schema(self) -> OrchestratorConfigSchema:
        """Return just the validated schema (used by orchestrator internally)."""
        row = await self.repo.get()
        if row and row.config:
            return OrchestratorConfigSchema.model_validate(row.config)
        return OrchestratorConfigSchema()

    async def update_config(self, data: dict) -> OrchestratorConfigResponse:
        """Validate and upsert the config from a dict."""
        schema = OrchestratorConfigSchema.model_validate(data)
        config_dict = schema.model_dump(mode="json")
        row = await self.repo.upsert(config_dict)
        return OrchestratorConfigResponse(
            config=schema, updated_at=row.updated_at
        )

    async def update_from_file(
        self, content: str, file_format: str
    ) -> OrchestratorConfigResponse:
        """Parse a YAML or JSON string and upsert."""
        data = self._parse_file_content(content, file_format)
        return await self.update_config(data)

    def _parse_file_content(self, content: str, file_format: str) -> dict:
        file_format = file_format.lower().strip(".")

        if file_format in ("json",):
            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                raise HTTPException(
                    status_code=422,
                    detail=f"Invalid JSON: {e.msg} at line {e.lineno}",
                )

        if file_format in ("yaml", "yml"):
            try:
                import yaml

                data = yaml.safe_load(content)
                if not isinstance(data, dict):
                    raise HTTPException(
                        status_code=422,
                        detail="YAML content must be a mapping/object at the top level",
                    )
                return data
            except yaml.YAMLError as e:
                raise HTTPException(
                    status_code=422, detail=f"Invalid YAML: {e}"
                )

        raise HTTPException(
            status_code=422,
            detail=f"Unsupported file format: '{file_format}'. Use .json, .yaml, or .yml",
        )
