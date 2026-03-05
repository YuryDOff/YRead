"""Cover-specific API endpoints (I2T reference analysis, etc.)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import AnalyzeCoverReferenceRequest, I2TAnalysisResult
from app.services.i2t_analysis_service import run_i2t_analysis
from app import crud

router = APIRouter()


@router.post("/books/{book_id}/analyze-cover-reference", response_model=I2TAnalysisResult)
async def analyze_cover_reference(
    book_id: int,
    body: AnalyzeCoverReferenceRequest,
    db: Session = Depends(get_db),
):
    """
    Runs GPT-4o Vision I2T analysis on a reference cover image.
    Stores result to CoverAnalysis DB record.
    Returns I2TAnalysisResult (all fields populated, or empty on Vision failure).
    """
    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    result = await run_i2t_analysis(image_url=body.image_url, mode=body.mode)

    cover_analysis = crud.get_or_create_cover_analysis(db, book_id)
    crud.update_cover_analysis(
        db,
        cover_analysis.id,
        reference_style_template=result.style_template,
        reference_style_notes={
            "composition_notes": result.composition_notes,
            "color_palette_extracted": result.color_palette_extracted,
            "style_tags": result.style_tags,
            "mood_keywords": result.mood_keywords,
            "lighting_description": result.lighting_description,
        },
        reference_image_url=body.image_url,
    )
    return result
