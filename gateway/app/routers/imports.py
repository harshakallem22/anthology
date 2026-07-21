"""Import upload and progress endpoints."""
from __future__ import annotations

import base64
import uuid

import httpx
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.security import current_user
from ..config import get_settings
from ..db import get_session
from ..models import Import, User
from ..schemas import ImportOut

router = APIRouter(prefix="/imports", tags=["imports"])
settings = get_settings()


def _detect_source(filename: str, explicit: str | None) -> str:
    if explicit in {"pocket", "instapaper"}:
        return explicit
    lower = (filename or "").lower()
    if lower.endswith(".html") or lower.endswith(".htm"):
        return "pocket"
    if "instapaper" in lower:
        return "instapaper"
    if lower.endswith(".csv"):
        return "instapaper"
    raise HTTPException(
        status_code=422,
        detail="Could not detect export source. Pass source=pocket|instapaper.",
    )


@router.post("", response_model=ImportOut, status_code=201)
async def create_import(
    file: UploadFile = File(...),
    source: str | None = Form(default=None),
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> Import:
    detected = _detect_source(file.filename or "", source)
    raw = await file.read()

    record = Import(
        user_id=user.id,
        source=detected,
        filename=file.filename,
        status="pending",
    )
    session.add(record)
    await session.commit()
    await session.refresh(record)

    payload = {
        "importId": str(record.id),
        "userId": str(user.id),
        "source": detected,
        "filename": file.filename,
        "fileContentBase64": base64.b64encode(raw).decode("ascii"),
    }
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(15.0, connect=5.0)) as client:
            resp = await client.post(
                f"{settings.extraction_service_url}/imports/ingest", json=payload
            )
            resp.raise_for_status()
    except httpx.HTTPError as exc:
        record.status = "failed"
        await session.commit()
        raise HTTPException(
            status_code=502, detail=f"Extraction service unavailable: {exc}"
        ) from exc

    return record


@router.get("/{import_id}", response_model=ImportOut)
async def get_import(
    import_id: uuid.UUID,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> Import:
    record = await session.get(Import, import_id)
    if record is None or record.user_id != user.id:
        raise HTTPException(status_code=404, detail="Import not found")
    return record
