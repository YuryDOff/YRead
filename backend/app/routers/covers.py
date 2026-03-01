"""Cover reference and generation endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.schemas import CoverAnalysisReferenceRequest, I2TAnalysisResult
from app.services.i2t_analysis_service import analyze_reference_image

router = APIRouter()


@router.post('/books/{book_id}/analyze-cover-reference', response_model=I2TAnalysisResult)
async def analyze_cover_reference(book_id: int, body: CoverAnalysisReferenceRequest, db: Session = Depends(get_db)):
    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail='Book not found')

    result = await analyze_reference_image(body.image_url, mode=body.mode)
    crud.create_or_update_cover_analysis(
        db,
        book_id,
        reference_style_template=result.style_template,
        reference_style_notes={
            'composition_notes': result.composition_notes,
            'color_palette_extracted': result.color_palette_extracted,
            'style_tags': result.style_tags,
            'mood_keywords': result.mood_keywords,
            'lighting_description': result.lighting_description,
        },
        reference_image_url=body.image_url,
    )
    return result
