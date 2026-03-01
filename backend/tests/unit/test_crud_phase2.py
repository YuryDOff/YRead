"""
Unit tests for Phase 2: CRUD extensions (artefacts, cover analysis, visual bible entries, cover concepts, entity activations).
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import CoverAnalysis, ChunkArtefact
from app import crud


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


def test_create_artefact_and_retrieve(db):
    book = crud.create_book(db, title="Test", author="A")
    a = crud.create_artefact(
        db,
        book_id=book.id,
        name="Magic Sword",
        physical_description="Glowing blade",
        symbolic_role="Power",
    )
    result = crud.get_artefacts_by_book(db, book.id)
    assert len(result) == 1
    assert result[0].name == "Magic Sword"


def test_update_artefact_partial(db):
    book = crud.create_book(db, title="Test", author="A")
    a = crud.create_artefact(
        db,
        book_id=book.id,
        name="Ring",
        symbolic_role="Originally empty",
    )
    crud.update_artefact(db, a.id, symbolic_role="Updated role")
    updated = crud.get_artefact(db, a.id)
    assert updated.symbolic_role == "Updated role"
    assert updated.name == "Ring"


def test_create_or_update_cover_analysis_upsert(db):
    book = crud.create_book(db, title="Test", author="A")
    crud.create_or_update_cover_analysis(db, book.id, thematic_statement="First")
    row1 = crud.get_cover_analysis(db, book.id)
    assert row1.thematic_statement == "First"
    crud.create_or_update_cover_analysis(db, book.id, thematic_statement="Second")
    rows = db.query(CoverAnalysis).filter(CoverAnalysis.book_id == book.id).all()
    assert len(rows) == 1
    assert rows[0].thematic_statement == "Second"


def test_get_active_entity_types_full_book(db):
    book = crud.create_book(db, title="Test", author="A")
    book.workflow_type = "full_book"
    db.commit()
    assert crud.get_active_entity_types(db, book.id) == ["cover", "characters", "locations", "artefacts"]


def test_get_active_entity_types_cover_only_default(db):
    book = crud.create_book(db, title="Test", author="A")
    book.workflow_type = "cover_only"
    db.commit()
    assert crud.get_active_entity_types(db, book.id) == ["cover"]


def test_get_active_entity_types_cover_only_activated(db):
    book = crud.create_book(db, title="Test", author="A")
    book.workflow_type = "cover_only"
    db.commit()
    crud.update_book_entity_activations(db, book.id, ["cover", "characters"])
    db.commit()
    assert "characters" in crud.get_active_entity_types(db, book.id)


def test_set_selected_cover_concept_exclusive(db):
    book = crud.create_book(db, title="Test", author="A")
    c1 = crud.create_cover_concept(db, book.id, 1, "prompt1", "", "illustrated")
    c2 = crud.create_cover_concept(db, book.id, 2, "prompt2", "", "abstract")
    crud.set_selected_cover_concept(db, book.id, c2.id)
    assert crud.get_cover_concept(db, c1.id).is_selected == 0
    assert crud.get_cover_concept(db, c2.id).is_selected == 1


def test_link_chunk_artefact_idempotent(db):
    book = crud.create_book(db, title="Test", author="A")
    chunks = crud.create_chunks_batch(db, book.id, [{"chunk_index": 0, "text": "Hello", "word_count": 1}])
    a = crud.create_artefact(db, book_id=book.id, name="Sword")
    crud.link_chunk_artefact(db, chunks[0].id, a.id)
    crud.link_chunk_artefact(db, chunks[0].id, a.id)  # second time
    count = db.query(ChunkArtefact).filter(
        ChunkArtefact.chunk_id == chunks[0].id,
        ChunkArtefact.artefact_id == a.id,
    ).count()
    assert count == 1


def test_visual_bible_entry_filter_by_entity(db):
    book = crud.create_book(db, title="Test", author="A")
    crud.create_visual_bible_entry(db, book.id, "character", 10, angle_label="front")
    crud.create_visual_bible_entry(db, book.id, "artefact", 1, angle_label="side")
    artefact_entries = crud.get_visual_bible_entries(db, book.id, entity_type="artefact")
    assert len(artefact_entries) == 1
    assert artefact_entries[0].entity_type == "artefact"
    assert artefact_entries[0].entity_id == 1
