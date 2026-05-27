import os
import time

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from app.dependencies.auth import get_current_user_context
from app.services.auth import UserContext

router = APIRouter(prefix="/uploads", tags=["uploads"])

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "svg"}
MAX_SIZE_BYTES = 2 * 1024 * 1024  # 2MB

UPLOADS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")


@router.post("/logo")
async def upload_logo(
    file: UploadFile,
    context: UserContext = Depends(get_current_user_context),
):
    """Upload a company logo image (png, jpg, svg). Max 2MB."""
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No file provided.")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    contents = await file.read()
    if len(contents) > MAX_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large. Maximum size is 2MB.",
        )

    os.makedirs(UPLOADS_DIR, exist_ok=True)

    timestamp = int(time.time())
    filename = f"logo-{context.tenant_id}-{timestamp}.{ext}"
    filepath = os.path.join(UPLOADS_DIR, filename)

    with open(filepath, "wb") as f:
        f.write(contents)

    return {"url": f"/uploads/{filename}"}
