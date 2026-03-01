from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app import crud
from app.services.ai_service import get_entity_types_for_mode


def _db():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_simple_mode_returns_only_characters():
    assert get_entity_types_for_mode('simple', ['character', 'location', 'artefact']) == ['character']


def test_pro_mode_returns_all_requested():
    types = ['character', 'location', 'artefact', 'scene']
    assert get_entity_types_for_mode('pro', types) == types


def test_simple_mode_ignores_requested_types():
    assert get_entity_types_for_mode('simple', ['artefact']) == ['character']


def test_default_mode_is_pro():
    db = _db()
    b = crud.create_book(db, title='Test', author='Author')
    assert b.analysis_mode == 'pro'
    db.close()


def test_simple_mode_persists():
    db = _db()
    b = crud.create_book(db, title='Test', author='Author', analysis_mode='simple')
    assert b.analysis_mode == 'simple'
    db.close()
