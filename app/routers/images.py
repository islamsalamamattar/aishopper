# app/routers/image.py
from fastapi import APIRouter, Path, HTTPException, Depends
from fastapi.responses import StreamingResponse
import httpx
from app.core.database import DBSessionDep
from app.utils.authUtils import authenticateToken

router = APIRouter(
    prefix="/image",
    tags=["Image"],
    responses={404: {"description": "Not found"}},
)

@router.get("/{image_url:path}", response_class=StreamingResponse)
async def fetch_image(
    image_url: str,
    db: DBSessionDep
):
    try:
        # Fetch the image from the CDN
        async with httpx.AsyncClient() as client:
            response = await client.get(image_url)
            response.raise_for_status()

        # Return the image as a streaming response
        return StreamingResponse(response.aiter_bytes(), media_type=response.headers.get("content-type"))
    
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=response.status_code, detail=f"Error fetching image: {str(e)}")
