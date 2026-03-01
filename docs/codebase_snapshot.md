# Codebase Snapshot — YRead / StoryForge AI

Comprehensive documentation for external AI (e.g. Claude) to produce implementation plans and test specifications. Exhaustive and precise; nothing omitted that would affect implementation decisions.

---

## 1. Project Structure

Full directory tree (2–3 levels). Folders with many similar files list all filenames explicitly.

```
YRead/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── crud.py
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── books.py
│   │   │   ├── visual_bible.py
│   │   │   ├── illustrations.py
│   │   │   ├── webhook.py
│   │   │   ├── scenes.py
│   │   │   └── settings.py
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── ai_service.py
│   │       ├── book_service.py
│   │       ├── upload_service.py
│   │       ├── search_service.py
│   │       ├── ontology_service.py
│   │       ├── ontology_constants.py
│   │       ├── artefact_analysis_service.py
│   │       ├── cover_analysis_service.py
│   │       ├── genre_defaults.py
│   │       ├── scene_extractor.py
│   │       ├── scene_visual_composer.py
│   │       ├── engine_selector.py
│   │       ├── openverse_auth.py
│   │       ├── providers/
│   │       │   ├── __init__.py
│   │       │   ├── base.py
│   │       │   ├── unsplash_provider.py
│   │       │   ├── serpapi_provider.py
│   │       │   ├── pexels_provider.py
│   │       │   ├── pixabay_provider.py
│   │       │   ├── openverse_provider.py
│   │       │   ├── wikimedia_provider.py
│   │       │   ├── deviantart_provider.py
│   │       │   ├── behance_provider.py
│   │       │   └── dribbble_provider.py
│   │       └── t2i_providers/
│   │           ├── __init__.py
│   │           ├── base.py
│   │           ├── abstract_provider.py
│   │           ├── sd_provider.py
│   │           └── flux_provider.py
│   ├── data/
│   │   ├── texts/
│   │   └── uploads/
│   ├── static/
│   │   ├── illustrations/
│   │   └── reference_uploads/
│   ├── scripts/
│   │   ├── reset_db.py
│   │   ├── openverse_register.py
│   │   └── run_reference_search_debug.py
│   ├── tests/
│   │   ├── unit/
│   │   │   ├── test_search_providers.py
│   │   │   ├── test_search_filter_rank.py
│   │   │   ├── test_bugs_enhancements_7_13.py
│   │   │   ├── test_query_diversification.py
│   │   │   ├── test_scene_visual_composer.py
│   │   │   ├── test_entity_token_builder.py
│   │   │   ├── test_provider_format_query.py
│   │   │   ├── test_scene_extractor.py
│   │   │   ├── test_engine_selector.py
│   │   │   ├── test_search_phase6.py
│   │   │   ├── test_ontology_service.py
│   │   │   ├── test_artefact_analysis.py
│   │   │   ├── test_cover_analysis.py
│   │   │   ├── test_models_phase1.py
│   │   │   ├── test_crud_phase2.py
│   │   │   └── test_bugs_phase7.py
│   │   ├── integration/
│   │   │   ├── test_analysis_phase5.py
│   │   │   ├── test_settings_and_analyze.py
│   │   │   └── test_scene_api.py
│   │   └── e2e/
│   │       └── test_e2e_pipeline_spec.py
│   ├── .env
│   ├── .env.example
│   └── (app.db, requirements, etc.)
├── frontend/
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── BookUpload.tsx
│   │   │   ├── BookReader.tsx
│   │   │   ├── LoadingScreen.tsx
│   │   │   ├── StyleSelector.tsx
│   │   │   ├── VisualBibleReview.tsx
│   │   │   ├── WorkflowLayout.tsx
│   │   │   └── WorkflowNav.tsx
│   │   ├── pages/
│   │   │   ├── HomePage.tsx
│   │   │   ├── SetupPage.tsx
│   │   │   ├── AnalysisReviewPage.tsx
│   │   │   ├── ReviewSearchPage.tsx
│   │   │   ├── ReviewSearchResultPage.tsx
│   │   │   ├── VisualBiblePage.tsx
│   │   │   ├── ReadingPage.tsx
│   │   │   └── SettingsPage.tsx
│   │   ├── context/
│   │   │   └── BookContext.tsx
│   │   ├── hooks/
│   │   │   └── useSettings.ts
│   │   └── services/
│   │       └── api.ts
│   └── package.json
├── docs/
│   ├── application_scope.md
│   └── codebase_snapshot.md (this file)
└── (Bugs and enhancements.md, debug-*.log, etc.)
```

Note: Legacy provider filenames (e.g. `openverse.py`, `pexels.py`, `wikimedia.py`, `pixabay.py`, `deviantart.py`) may exist under `backend/app/services/providers/` as older versions; the active implementations are the `*_provider.py` files listed above.

---

## 2. Backend: Database Schema

All SQLAlchemy models and raw table definitions. Column types, nullability, defaults, constraints, relationships, indexes. JSON column schemas where documented.

### 2.1 Models (app/models.py)

**Table: `scenes`**
| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | Integer | NO | autoincrement | PK |
| book_id | Integer | NO | — | FK(books.id) |
| title | String | YES | — | — |
| title_display | String | YES | — | — |
| scene_type | String | YES | — | — |
| chunk_start_index | Integer | NO | — | — |
| chunk_end_index | Integer | NO | — | — |
| narrative_summary | Text | YES | — | — |
| narrative_summary_display | Text | YES | — | — |
| visual_description | Text | YES | — | — |
| dramatic_score_avg | Float | YES | — | — |
| visual_intensity | Float | YES | — | — |
| illustration_priority | String | YES | — | — |
| narrative_position | String | YES | — | — |
| scene_prompt_draft | Text | YES | — | — |
| scene_visual_tokens_json | Text | YES | — | — |
| t2i_prompt_json | Text | YES | — | — |
| is_selected | Integer | — | 1 | — |
| created_at | DateTime | — | datetime.utcnow | — |

- **Relationships:** book → Book; scene_characters → SceneCharacter; scene_locations → SceneLocation; scene_artefacts → SceneArtefact; illustrations → Illustration.
- **Indexes:** ix_scenes_book_id (book_id).

**Table: `scene_characters`**
| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | Integer | NO | autoincrement, PK |
| scene_id | Integer | NO | FK(scenes.id) |
| character_id | Integer | NO | FK(characters.id) |

- **UniqueConstraint:** uq_scene_character (scene_id, character_id).
- **Relationships:** character → Character.

**Table: `scene_locations`**
| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | Integer | NO | autoincrement, PK |
| scene_id | Integer | NO | FK(scenes.id) |
| location_id | Integer | NO | FK(locations.id) |

- **UniqueConstraint:** uq_scene_location (scene_id, location_id).
- **Relationships:** location → Location.

**Table: `engine_ratings`**
| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | Integer | NO | autoincrement, PK |
| book_id | Integer | NO | FK(books.id) |
| provider | String | NO | — |
| likes | Integer | — | 0 |
| dislikes | Integer | — | 0 |

- **Property:** net_score = likes - dislikes.
- **UniqueConstraint:** uq_engine_rating (book_id, provider).
- **Index:** ix_engine_ratings_book_id (book_id).

**Table: `books`**
| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | Integer | NO | autoincrement, PK |
| title | String | NO | — |
| author | String | YES | — |
| google_drive_link | Text | YES | — |
| file_path | Text | YES | — |
| total_words | Integer | YES | — |
| total_pages | Integer | YES | — |
| status | String | — | "imported" |
| is_well_known | Integer | — | 0 |
| workflow_type | String | — | "full" |
| is_well_known_book | Boolean | — | False |
| well_known_book_title | Text | YES | — |
| similar_book_title | Text | YES | — |
| scene_count | Integer | YES | 10 |
| scene_display_count | Integer | — | 10 |
| target_audience | String | — | "adult" |
| search_query_strategy | String | — | "tokens" |
| known_adaptations_json | Text | YES | — |
| entity_activations | Text | YES | — |
| genre | Text | YES | — |
| created_at | DateTime | — | datetime.utcnow |
| updated_at | DateTime | — | datetime.utcnow, onupdate=datetime.utcnow |

- **Relationships:** chunks, characters, locations, visual_bible, illustrations, covers, kdp_exports, search_queries, scenes, engine_ratings, artefacts, cover_analysis (one), visual_bible_entries, cover_concepts (all cascade delete-orphan where applicable).
- **Phase 7:** scene_display_count = how many scenes to show in UI (extraction uses total_words); target_audience = children|ya|adult|literary; search_query_strategy = tokens|adaptive for reference search.

**Table: `chunks`**
| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | Integer | NO | autoincrement, PK |
| book_id | Integer | NO | FK(books.id) |
| chunk_index | Integer | NO | — |
| text | Text | NO | — |
| start_page | Integer | YES | — |
| end_page | Integer | YES | — |
| word_count | Integer | YES | — |
| dramatic_score | Float | YES | — |
| visual_analysis_json | Text | YES | — |

- **Relationships:** book → Book; illustrations; chunk_characters; chunk_locations; chunk_artefacts.
- **Indexes:** ix_chunks_book_id (book_id), ix_chunks_book_index (book_id, chunk_index).
- **JSON (visual_analysis_json):** implicit schema: `{ "visual_layers": {...}, "visual_tokens": {...} }` (see chunk_analyses in ai_service / schemas).

**Table: `characters`**
| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | Integer | NO | autoincrement, PK |
| book_id | Integer | NO | FK(books.id) |
| name | String | NO | — |
| physical_description | Text | YES | — |
| personality_traits | Text | YES | — |
| typical_emotions | Text | YES | — |
| reference_image_url | Text | YES | — |
| selected_reference_urls | Text | YES | — |
| is_main | Integer | — | 0 |
| visual_type | String | YES | — |
| is_well_known_entity | Integer | — | 0 |
| canonical_search_name | String | YES | — |
| search_visual_analog | Text | YES | — |
| text_to_image_prompt | Text | YES | — |
| ontology_json | Text | YES | — |
| entity_visual_tokens_json | Text | YES | — |
| cover_role | Integer | — | 0 |
| visual_bible_depth | Integer | YES | — |
| is_selected_for_reference | Integer | — | 0 |
| full_description | Text | YES | — |

- **Relationships:** book → Book; chunk_characters.
- **Index:** ix_characters_book_id (book_id).
- **JSON:** selected_reference_urls = array of strings; ontology_json / entity_visual_tokens_json shapes match ontology_service and ai_service entity token output.
- **Phase 7:** is_selected_for_reference = UI selection for reference search (never overwrite is_main); full_description = 1–2 sentence visual description for search/generation.

**Table: `locations`**
| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | Integer | NO | autoincrement, PK |
| book_id | Integer | NO | FK(books.id) |
| name | String | NO | — |
| visual_description | Text | YES | — |
| atmosphere | Text | YES | — |
| reference_image_url | Text | YES | — |
| selected_reference_urls | Text | YES | — |
| is_main | Integer | — | 0 |
| is_well_known_entity | Integer | — | 0 |
| canonical_search_name | String | YES | — |
| search_visual_analog | Text | YES | — |
| text_to_image_prompt | Text | YES | — |
| ontology_json | Text | YES | — |
| entity_visual_tokens_json | Text | YES | — |
| cover_role | Integer | — | 0 |
| visual_bible_depth | Integer | YES | — |
| is_selected_for_reference | Integer | — | 0 |
| full_description | Text | YES | — |

- **Relationships:** book → Book; chunk_locations.
- **Index:** ix_locations_book_id (book_id).
- **Phase 7:** is_selected_for_reference, full_description (same semantics as characters).

**Table: `artefacts`**
| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | Integer | NO | autoincrement, PK |
| book_id | Integer | NO | FK(books.id) |
| name | String | NO | — |
| physical_description | Text | YES | — |
| symbolic_role | Text | YES | — |
| narrative_function | String | YES | — |
| typical_contexts | Text | YES | — |
| is_main | Integer | — | 0 |
| visual_type | String | YES | — |
| is_well_known_entity | Integer | — | 0 |
| canonical_search_name | String | YES | — |
| search_visual_analog | Text | YES | — |
| text_to_image_prompt | Text | YES | — |
| ontology_json | Text | YES | — |
| entity_visual_tokens_json | Text | YES | — |
| reference_image_url | Text | YES | — |
| selected_reference_urls | Text | YES | — |
| visual_bible_images | Text | YES | — |
| visual_bible_depth | Integer | YES | — |
| is_selected_for_reference | Integer | — | 0 |
| full_description | Text | YES | — |

- **Relationships:** book → Book.
- **Index:** ix_artefacts_book_id (book_id).
- **Phase 7:** is_selected_for_reference, full_description.

**Table: `chunk_artefacts`**
| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | Integer | NO | autoincrement, PK |
| chunk_id | Integer | NO | FK(chunks.id) |
| artefact_id | Integer | NO | FK(artefacts.id) |

- **UniqueConstraint:** uq_chunk_artefact (chunk_id, artefact_id).
- **Indexes:** ix_chunk_artefacts_chunk_id, ix_chunk_artefacts_artefact_id.

**Table: `scene_artefacts`**
| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | Integer | NO | autoincrement, PK |
| scene_id | Integer | NO | FK(scenes.id) |
| artefact_id | Integer | NO | FK(artefacts.id) |

- **UniqueConstraint:** uq_scene_artefact (scene_id, artefact_id).

**Table: `cover_analysis`**
| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | Integer | NO | autoincrement, PK |
| book_id | Integer | NO | FK(books.id), unique |
| thematic_statement | Text | YES | — |
| emotional_promise | Text | YES | — |
| dominant_motifs | Text | YES | — |
| symbolic_anchors | Text | YES | — |
| cover_mood_keywords | Text | YES | — |
| genre_conventions | Text | YES | — |
| genre_subversion_opportunity | Text | YES | — |
| typography_direction | Text | YES | — |
| color_palette_direction | Text | YES | — |
| cover_t2i_prompt | Text | YES | — |
| cover_negative_prompt | Text | YES | — |
| cover_role_character_ids | Text | YES | — |
| cover_role_location_ids | Text | YES | — |
| cover_role_artefact_ids | Text | YES | — |
| cover_type | String | YES | — |
| color_palette_structured | Text | YES | — |
| primary_cover_character_id | Integer | YES | — |
| primary_cover_location_id | Integer | YES | — |
| primary_cover_artefact_id | Integer | YES | — |
| full_description | Text | YES | — |
| created_at | DateTime | — | datetime.utcnow |
| updated_at | DateTime | — | datetime.utcnow, onupdate=datetime.utcnow |

- **Index:** ix_cover_analysis_book_id (book_id).
- **Phase 7:** cover_type = object_centered|character_centered|setting_centered|abstract|typography_centered; color_palette_structured = JSON (dominant, accent, temperature, contrast, saturation); primary_cover_*_id = single focal entity; full_description for search/generation.

**Table: `visual_bible_entries`**
| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | Integer | NO | autoincrement, PK |
| book_id | Integer | NO | FK(books.id) |
| entity_type | String | NO | — |
| entity_id | Integer | NO | — |
| angle_label | String | YES | — |
| prompt_used | Text | YES | — |
| image_path | Text | YES | — |
| status | String | — | "pending" |
| is_approved | Integer | — | 0 |
| created_at | DateTime | — | datetime.utcnow |

- **Index:** ix_vb_entries_book_entity (book_id, entity_type, entity_id).

**Table: `cover_concepts`**
| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | Integer | NO | autoincrement, PK |
| book_id | Integer | NO | FK(books.id) |
| concept_index | Integer | NO | — |
| prompt_used | Text | YES | — |
| negative_prompt | Text | YES | — |
| style_variant | String | YES | — |
| image_path | Text | YES | — |
| status | String | — | "pending" |
| is_selected | Integer | — | 0 |
| created_at | DateTime | — | datetime.utcnow |

- **Index:** ix_cover_concepts_book_id (book_id).

**Table: `visual_bible`**
| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | Integer | NO | autoincrement, PK |
| book_id | Integer | NO | FK(books.id), unique |
| style_category | String | YES | — |
| tone_description | Text | YES | — |
| illustration_frequency | Integer | YES | — |
| layout_style | String | YES | — |
| approved_at | DateTime | YES | — |

- **Relationships:** book → Book.

**Table: `illustrations`**
| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | Integer | NO | autoincrement, PK |
| book_id | Integer | NO | FK(books.id) |
| chunk_id | Integer | YES | FK(chunks.id) |
| scene_id | Integer | YES | FK(scenes.id) |
| page_number | Integer | YES | — |
| image_path | Text | YES | — |
| prompt | Text | YES | — |
| prompt_used | Text | YES | — |
| style | String | YES | — |
| reference_images | Text | YES | — |
| status | String | — | "pending" |
| created_at | DateTime | — | datetime.utcnow |

- **Relationships:** book → Book; chunk → Chunk; scene → Scene.
- **Indexes:** ix_illustrations_book_id (book_id), ix_illustrations_status (status).

**Table: `covers`**
| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | Integer | NO | autoincrement, PK |
| book_id | Integer | NO | FK(books.id) |
| front_visual_path | Text | YES | — |
| full_cover_path | Text | YES | — |
| template | String | YES | — |
| spine_width | Float | YES | — |
| customizations | Text | YES | — |
| generated_at | DateTime | — | datetime.utcnow |

- **Index:** ix_covers_book_id (book_id).

**Table: `kdp_exports`**
| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | Integer | NO | autoincrement, PK |
| book_id | Integer | NO | FK(books.id) |
| trim_size | String | YES | — |
| interior_pdf_path | Text | YES | — |
| cover_pdf_path | Text | YES | — |
| zip_file_path | Text | YES | — |
| exported_at | DateTime | — | datetime.utcnow |
| download_count | Integer | — | 0 |

- **Index:** ix_kdp_exports_book_id (book_id).

**Table: `search_queries`**
| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | Integer | NO | autoincrement, PK |
| book_id | Integer | NO | FK(books.id) |
| entity_type | String | NO | — |
| entity_name | String | NO | — |
| query_text | Text | NO | — |
| results_count | Integer | — | 0 |
| provider | String | YES | — |
| created_at | DateTime | — | datetime.utcnow |

- **Index:** ix_search_queries_book_id (book_id).

**Table: `reference_images`**
| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | Integer | NO | autoincrement, PK |
| book_id | Integer | NO | — |
| entity_type | String | NO | — |
| entity_id | Integer | NO | — |
| url | Text | NO | — |
| thumbnail | Text | YES | — |
| width | Integer | YES | — |
| height | Integer | YES | — |
| source | String | NO | — |
| created_at | DateTime | — | datetime.utcnow |

- **Indexes:** ix_reference_images_book_entity (book_id, entity_type, entity_id), ix_reference_images_entity_created (entity_type, entity_id, created_at).
- **entity_type:** `"character"` | `"location"` | `"artefact"` | `"cover"`. No FK to characters/locations/artefacts; entity_id refers to the corresponding entity id by convention (e.g. character.id, location.id, artefact.id; for cover, cover_analysis.id or agreed identifier).

**Table: `chunk_characters`**
| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | Integer | NO | autoincrement, PK |
| chunk_id | Integer | NO | FK(chunks.id) |
| character_id | Integer | NO | FK(characters.id) |

- **UniqueConstraint:** uq_chunk_character (chunk_id, character_id).
- **Indexes:** ix_chunk_characters_chunk_id, ix_chunk_characters_character_id.

**Table: `chunk_locations`**
| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | Integer | NO | autoincrement, PK |
| chunk_id | Integer | NO | FK(chunks.id) |
| location_id | Integer | NO | FK(locations.id) |

- **UniqueConstraint:** uq_chunk_location (chunk_id, location_id).
- **Indexes:** ix_chunk_locations_chunk_id, ix_chunk_locations_location_id.

### 2.2 Migrations: _run_migrations() (app/database.py)

Full content of `_run_migrations()`:

- **Existing migrations:**  
  - characters: is_main INTEGER DEFAULT 0  
  - locations: is_main INTEGER DEFAULT 0  
- **B2B books:** workflow_type TEXT DEFAULT 'full'; is_well_known_book BOOLEAN DEFAULT 0; well_known_book_title TEXT; similar_book_title TEXT  
- **Task 1.6:** search_queries.provider TEXT; chunks.visual_analysis_json TEXT  
- **Smart visual query:** characters: visual_type, is_well_known_entity INTEGER DEFAULT 0, canonical_search_name, search_visual_analog; locations: is_well_known_entity, canonical_search_name, search_visual_analog  
- **Text-to-image:** characters.text_to_image_prompt, locations.text_to_image_prompt  
- **Review Search Result:** characters.selected_reference_urls, locations.selected_reference_urls  
- **v3 ontology/tokens:** characters/locations: ontology_json, entity_visual_tokens_json  
- **v3 book:** books.scene_count INTEGER DEFAULT 10, books.known_adaptations_json TEXT  
- **v3 illustrations:** illustrations.scene_id INTEGER, illustrations.prompt_used TEXT  
- **Scene display:** scenes.title_display TEXT, scenes.narrative_summary_display TEXT  
- **Phase 1 (Four-entity model):** books.entity_activations TEXT, books.genre TEXT; characters.cover_role INTEGER DEFAULT 0, characters.visual_bible_depth INTEGER; locations.cover_role INTEGER DEFAULT 0, locations.visual_bible_depth INTEGER. New tables (artefacts, chunk_artefacts, scene_artefacts, cover_analysis, visual_bible_entries, cover_concepts) created via Base.metadata.create_all.
- **Phase 5:** clear_analysis_results also deletes artefacts, chunk_artefacts, scene_artefacts, and cover_analysis for the book when full entity set is requested.
- **Phase 7 BUG-1:** characters.is_selected_for_reference INTEGER DEFAULT 0, locations.is_selected_for_reference INTEGER DEFAULT 0, artefacts.is_selected_for_reference INTEGER DEFAULT 0.
- **Phase 7 BUG-2:** books.scene_display_count INTEGER DEFAULT 10, books.target_audience TEXT DEFAULT 'adult'.
- **Phase 7.1:** cover_analysis.cover_type, color_palette_structured, primary_cover_character_id, primary_cover_location_id, primary_cover_artefact_id.
- **Phase 7.5:** characters/locations/artefacts/cover_analysis.full_description TEXT; books.search_query_strategy TEXT DEFAULT 'tokens'.
- **Deprecated:** _drop_table_if_exists("reading_progress")

Helper: `_add_column_if_missing(table, column, col_type)` uses SQLAlchemy inspect to check columns and runs `ALTER TABLE ... ADD COLUMN` if missing. `_drop_table_if_exists(table)` drops the table if it exists.

---

## 3. Backend: API Endpoints

For every FastAPI router: HTTP method, full path, path/query/body types, response schema, service functions called, implementation status, background tasks.

**Base prefix for all API routes:** `/api` (from main.py).

### 3.1 Health (main.py)

| Method | Path | Params | Body | Response | Service | Status |
|--------|------|--------|------|----------|---------|--------|
| GET | /health | — | — | `{ status, app }` | — | Complete |

### 3.2 Books router (app/routers/books.py)

| Method | Path | Params | Body | Response | Service / CRUD | Status |
|--------|------|--------|------|----------|----------------|--------|
| POST | /api/manuscripts/upload | — | file: UploadFile | BookResponse | upload_service.process_manuscript_upload, crud.create_book, crud.update_book | Complete |
| POST | /api/books/import | — | BookImportRequest | BookResponse | book_service.download_text_from_google_drive, compute_metadata, guess_title; crud.create_book, update_book | Complete |
| GET | /api/books/{book_id} | book_id: int | — | BookResponse | crud.get_book | Complete |
| GET | /api/books | skip: int=0, limit: int=100 | — | list[BookResponse] | crud.get_books | Complete |
| DELETE | /api/books/{book_id} | book_id: int | — | StatusResponse | crud.delete_book | Complete |
| POST | /api/books/{book_id}/chunk | book_id: int | — | StatusResponse | book_service.chunk_text; crud.* chunks | Complete |
| POST | /api/books/{book_id}/analyze | book_id: int | BookAnalyzeRequest | AnalyzeStatusResponse (202) | crud.*; BackgroundTasks → _run_analysis_background (entity_types: characters, locations, artefacts, cover; selective clear; run_full_analysis, artefact_analysis_service, cover_analysis_service; persist) | Complete |
| GET | /api/books/{book_id}/analysis-progress | book_id: int | — | `{ overall_status, entity_progress: { entity_type: { status, current, total } } }` (or 404) | In-memory _analysis_progress dict | Complete |
| POST | /api/books/{book_id}/analyze/entity | book_id: int | AnalyzeEntityRequest | AnalyzeStatusResponse (202) | BackgroundTasks → _run_analysis_background for single entity_type | Complete |
| GET | /api/books/{book_id}/artefacts | book_id: int | — | list[ArtefactResponse] | crud.get_artefacts_by_book | Complete |
| PUT | /api/books/{book_id}/artefacts/{artefact_id} | book_id, artefact_id: int | ArtefactUpdate | ArtefactResponse | crud.get_artefact, update_artefact | Complete |
| PUT | /api/books/{book_id}/entity-activations | book_id: int | EntityActivationsRequest | StatusResponse | crud.update_book_entity_activations | Complete |
| GET | /api/books/{book_id}/characters | book_id: int | — | list[CharacterResponse] | crud.get_characters_by_book | Complete |
| GET | /api/books/{book_id}/locations | book_id: int | — | list[LocationResponse] | crud.get_locations_by_book | Complete |
| PUT | /api/books/{book_id}/entity-selections | book_id: int | EntitySelectionsRequest | StatusResponse | crud.update_entity_reference_selection (writes is_selected_for_reference only; never is_main) | Complete |
| GET | /api/books/{book_id}/chunks | book_id: int | — | list[ChunkResponse] | crud.get_chunks_by_book | Complete |
| GET | /api/books/{book_id}/search-queries | book_id: int | — | list[SearchQueryResponse] | crud.get_search_queries_by_book | Complete |

**BookAnalyzeRequest:** style_category, illustration_frequency, layout_style, is_well_known, author?, well_known_book_title?, similar_book_title?, scene_count=10, scene_display_count=10, target_audience="adult", search_query_strategy="tokens", entity_types=["cover","characters","locations","artefacts"], genre="".

**EntitySelectionsRequest:** characters: list[EntityMainFlag], locations: list[EntityMainFlag]; EntityMainFlag: id, is_main.

**EntityActivationsRequest:** entity_activations: list[str]. **AnalyzeEntityRequest:** entity_type: str. **ArtefactUpdate:** optional name, physical_description, symbolic_role, narrative_function, typical_contexts, is_main, visual_type.

### 3.3 Visual Bible router (app/routers/visual_bible.py)

| Method | Path | Params | Body | Response | Service / CRUD | Status |
|--------|------|--------|------|----------|----------------|--------|
| GET | /api/books/{book_id}/visual-bible | book_id: int | — | `{ visual_bible, characters, locations }` (characters/locations include selected_reference_urls) | crud.get_book, get_visual_bible, get_characters_by_book, get_locations_by_book | Complete |
| GET | /api/books/{book_id}/proposed-search-queries | book_id: int, main_only: bool=True | — | `{ characters, locations, scenes, artefacts, cover: {proposed_queries, cover_analysis_summary}? }` | search_service.get_proposed_search_queries | Complete |
| PATCH | /api/books/{book_id}/entity-summaries | book_id: int | EntitySummariesUpdate | `{ status }` | crud.update_character, update_location | Complete |
| POST | /api/books/{book_id}/search-references | book_id: int | SearchReferencesRequest? | `{ characters, locations, artefacts, cover: {cover: images[]}, queries_run, provider_usage }` | search_service.search_references_for_book; crud (reference_images, trim_reference_images_fifo) | Complete |
| GET | /api/books/{book_id}/reference-results | book_id: int | — | `{ cover: {cover: images[]}, characters, locations, artefacts: {entityName: images[]} }` (cover first to avoid truncation) | crud.get_reference_images_for_entity, get_cover_analysis | Complete |
| POST | /api/books/{book_id}/visual-bible/approve | book_id: int | VisualBibleApproveRequest | StatusResponse | crud.update_character/update_location/update_artefact (reference_image_url, selected_reference_urls), approve_visual_bible | Complete |
| POST | /api/books/{book_id}/reference-upload | book_id: int | Form: entity_type (character\|location\|artefact\|cover), entity_id, file | `{ url, thumbnail, source, id }` | crud.create_reference_image, trim_reference_images_fifo | Complete |
| PATCH | /api/books/{book_id}/engine-ratings | book_id: int | EngineRatingUpdate | StatusResponse | crud.update_engine_rating | Complete |
| GET | /api/books/{book_id}/engine-ratings | book_id: int | — | list[EngineRatingResponse] | crud.get_engine_ratings_list | Complete |
| GET | /api/books/{book_id}/cover-analysis | book_id: int | — | CoverAnalysisResponse (404 if not run) | crud.get_cover_analysis | Complete |
| PATCH | /api/books/{book_id}/cover-analysis | book_id: int | CoverAnalysisUpdateRequest | CoverAnalysisResponse | crud.create_or_update_cover_analysis | Complete |
| GET | /api/books/{book_id}/visual-bible/entries | book_id: int, entity_type?, entity_id? | — | list[VisualBibleEntryResponse] | crud.get_visual_bible_entries | Complete |
| POST | /api/books/{book_id}/visual-bible/entries/generate | book_id: int | VisualBibleEntryGenerateRequest | VisualBibleEntryResponse (202) | crud.create_visual_bible_entry; BackgroundTasks → T2I stub | Complete |
| POST | /api/books/{book_id}/visual-bible/entries/generate-all | book_id: int | VisualBibleEntryGenerateAllRequest? | { queued, entries } | crud.create_visual_bible_entry per angle; BackgroundTasks | Complete |
| PATCH | /api/books/{book_id}/visual-bible/entries/{entry_id} | book_id, entry_id: int | VisualBibleEntryPatchRequest | VisualBibleEntryResponse | crud.update_visual_bible_entry | Complete |

**SearchReferencesRequest:** main_only=True, character_queries?, location_queries?, character_summaries?, location_summaries?, preferred_provider?: "unsplash"|"serpapi", search_entity_types?: "characters"|"locations"|"both"|"artefacts"|"cover"|"all", enabled_providers?: list[str].

**VisualBibleApproveRequest:** character_selections: dict[str, list[str]], location_selections: dict[str, list[str]], artefact_selections: dict[str, list[str]], cover_selections: list[str].

### 3.4 Scenes router (app/routers/scenes.py)

| Method | Path | Params | Body | Response | Service / CRUD | Status |
|--------|------|--------|------|----------|----------------|--------|
| GET | /api/books/{book_id}/scenes | book_id: int, show_all: bool=False | — | list[SceneResponse] | crud.get_book; _load_scenes_with_relations; sorted by dramatic importance; if not show_all, limit to book.scene_display_count (default 10) | Complete |
| PATCH | /api/books/{book_id}/scenes/{scene_id} | book_id, scene_id: int | SceneUpdateRequest | SceneResponse | crud.update_scene | Complete |
| POST | /api/books/{book_id}/scenes/{scene_id}/generate-illustration | book_id, scene_id: int | — | StatusResponse (202) | crud.get_book, get_scene | **Stub** — returns "Illustration generation queued (T2I provider not yet configured)" |

**SceneUpdateRequest:** title?, scene_prompt_draft?, is_selected?.

### 3.5 Settings router (app/routers/settings.py)

| Method | Path | Params | Body | Response | Service | Status |
|--------|------|--------|------|----------|---------|--------|
| GET | /api/settings/providers | — | — | `{ providers: [{ name, label, available }] }` | ALL_PROVIDERS[*].is_available() | Complete |

### 3.6 Illustrations router (app/routers/illustrations.py)

| Method | Path | Params | Body | Response | Service / CRUD | Status |
|--------|------|--------|------|----------|----------------|--------|
| GET | /api/books/{book_id}/cover-concepts | book_id: int | — | list[CoverConceptResponse] | crud.get_cover_concepts | Complete |
| POST | /api/books/{book_id}/cover-concepts/generate | book_id: int | CoverConceptGenerateRequest? | { queued, concepts } | crud.create_cover_concept × concept_count; default prompt from cover_analysis.cover_t2i_prompt; BackgroundTasks → T2I stub | Complete |
| PATCH | /api/books/{book_id}/cover-concepts/{concept_id} | book_id, concept_id: int | CoverConceptPatchRequest | CoverConceptResponse | crud.update_cover_concept | Complete |
| POST | /api/books/{book_id}/cover-concepts/{concept_id}/select | book_id, concept_id: int | — | StatusResponse | crud.set_selected_cover_concept | Complete |

### 3.7 Webhook router (app/routers/webhook.py)

- Router is empty: only `router = APIRouter()`. No endpoints. **Stub.**

### 3.8 Background tasks

- **startup:** init_db(), start_background_refresh() (Openverse token refresh thread).
- **POST /api/books/{book_id}/analyze:** BackgroundTasks.add_task(_run_analysis_background, book_id, req_dict). Book is updated with scene_count from request (persisted for re-runs). _run_analysis_background runs jobs per entity_types (characters+locations → run_full_analysis; artefacts and cover may run in parallel via ThreadPoolExecutor). Selective clear per type. When persisting: main_characters and main_locations are capped to MAX_MAIN_CHARACTERS and MAX_MAIN_LOCATIONS (ai_service); scenes created from pipeline output are capped to scene_count_to_use (only first scene_count_to_use scenes are written). Progress updates are thread-safe: all writes to _analysis_progress use _progress_lock and _update_entity_progress(book_id, entity_type, status, current, total); overall_status uses _set_overall_status(book_id, status). Scene extraction is skipped only when workflow_type is cover_only and "characters" is not in entity_types (scene_count_to_use = 0); otherwise scene_count from request is passed to run_full_analysis.

---

## 4. Backend: Service Layer

For each file in services/ (and subdirectories): purpose, public functions (signature, params, return, 2–3 sentence description), external API calls, DB operations, in-memory state.

### 4.1 ai_service.py

**Purpose:** AI analysis of manuscript chunks via OpenAI: batch chunk analysis, consolidation of characters/locations, ontology classification, entity visual tokens, scene extraction, scene visual composition.

**Constants:** MAX_MAIN_CHARACTERS = 5, MAX_MAIN_LOCATIONS = 5. Consolidation output is limited to these counts; re-runs can yield different secondary characters due to model non-determinism. The consolidation prompt instructs the model to pick consistently by mention frequency to reduce variance between re-runs.

**Public functions:**

- `calculate_dramatic_score(text, action_level, emotional_intensity, visual_richness) -> float`  
  Combines LLM scores with keyword bonuses/penalties; returns 0.0–1.0.

- `assess_visual_density(text) -> str`  
  Returns "low"|"medium"|"high" based on visual adjective density.

- `detect_narrative_position(chunk_index, total_chunks) -> str`  
  Returns opening_hook | inciting_incident | rising_action | midpoint | climax | resolution.

- `calculate_character_priority(characters_present, main_characters) -> float`  
  Returns 1.0 / 0.8 / 0.5 based on main character presence.

- `build_visual_tokens(visual_layers) -> dict`  
  Builds core_tokens, style_tokens, technical_tokens from visual_layers dict.

- `detect_manuscript_language(chunks, sample_chars=4000) -> str`  
  Uses langdetect on concatenated chunk text; returns ISO 639-1 or "en".

- `build_entity_visual_tokens_batch(entities) -> list[dict]`  
  Single batched OpenAI call; input list of entity dicts, output same order with core_tokens, style_tokens, archetype_tokens, anti_tokens.

- `analyze_chunk_batch(chunks, run_id=None) -> dict`  
  GPT call with BATCH_ANALYSIS_PROMPT; chunks = [{chunk_index, text}]. Returns {characters, locations, chunk_analyses}.

- `consolidate_results(all_batch_results, is_well_known_book=False, run_id=None) -> dict`  
  Single GPT call; returns {main_characters, main_locations, tone_and_style, known_adaptations}.

- `run_full_analysis(chunks, progress_callback=None, scene_count=10, is_well_known_book=False, analysis_run_id=None) -> dict`  
  Full pipeline: batch analysis → consolidation → ontology_service.classify_entities_batch → entity visual tokens → post-process chunk_analyses → scene_extractor.extract_scenes → scene_visual_composer.compose_scenes_batch. Returns consolidated dict with main_characters, main_locations, tone_and_style, chunk_analyses, scenes.

**External API:** OpenAI `client.chat.completions.create` (model from OPENAI_MODEL, default gpt-4o-mini). Used for batch analysis, consolidation, entity visual tokens.

**DB:** None (stateless; callers persist).

**In-memory:** Module-level `_client: Optional[OpenAI]` lazy-initialized.

### 4.2 book_service.py

**Purpose:** Book import from Google Drive, metadata, chunking.

**Public functions:**

- `extract_file_id(google_drive_link) -> Optional[str]`  
  Regex extract of Google Drive file ID.

- `build_direct_download_url(file_id) -> str`  
  Returns uc?export=download URL.

- `download_text_from_google_drive(google_drive_link) -> str`  
  Async httpx get; validates content-type and size; returns text. Raises ValueError/RuntimeError.

- `compute_metadata(text) -> dict`  
  Returns {total_words, total_pages} (WORDS_PER_PAGE = 300).

- `chunk_text(text, target_tokens=2000, overlap_tokens=200) -> list[dict]`  
  Splits by paragraphs with tiktoken; returns [{chunk_index, text, start_page, end_page, word_count}].

- `guess_title(text, filename=None) -> str`  
  From filename stem or first non-empty line.

**External API:** Google Drive download (httpx). No DB. Cached `_encoder` (tiktoken) at module level.

### 4.3 upload_service.py

**Purpose:** Manuscript file upload: validate, save, extract text from .txt/.docx/.pdf, compute metadata.

**Public functions:**

- `validate_file(filename, file_size) -> None`  
  Raises UploadError if ext not in .txt/.docx/.pdf or size > 20MB.

- `process_manuscript_upload(file_content, filename, upload_dir) -> Tuple[str, dict]`  
  Validates, saves file, extracts text via extract_text_from_*, returns (text, {title, word_count, estimated_pages, original_filename}).

- `extract_text_from_txt(file_path) -> str`  
- `extract_text_from_docx(file_path) -> str` (python-docx)  
- `extract_text_from_pdf(file_path) -> str` (PyPDF2)  
- `extract_text_from_file(file_path, extension) -> str`  
- `guess_title_from_text(text, filename) -> str`  
- `compute_word_count(text) -> int`  
- `estimate_page_count(word_count, words_per_page=250) -> int`  
- `save_uploaded_file(file_content, filename, upload_dir) -> str`  

**External API:** None. **DB:** None. **In-memory:** None.

### 4.4 search_service.py

**Purpose:** Reference image search: multi-provider (Unsplash, SerpAPI, Pexels, Pixabay, Openverse, Wikimedia, DeviantArt, Behance, Dribbble), query building/diversification, filter/rank, persist queries and reference_images. Supports characters, locations, artefacts, and cover.

**Public functions:**

- `get_proposed_search_queries(book_id, db, main_only=True) -> dict`  
  Builds proposed query list per main (or all) character/location/artefact and cover; uses stored queries or _build_queries_diversified / _build_queries / _build_queries_artefact / _build_cover_queries. Returns {characters, locations, scenes, artefacts, cover: {proposed_queries, cover_analysis_summary}?}.

- `search_references_for_book(book_id, search_all=False, db=None, ..., search_entity_types="both"|"artefacts"|"cover"|"all", ...) -> dict`  
  Updates DB from summaries; selects entities to search (characters, locations, artefacts, cover per search_entity_types); for each entity builds queries, uses select_engines for artefact/cover provider mix, _search_all_providers/_search_entity, filter/dedupe/rank, _save_query; assign_placeholder for non-searched character/location. Returns {book_id, mode, characters, locations, artefacts, cover?, queries_run, provider_usage}.

**Constants exported:** CHARACTER_PLACEHOLDER, LOCATION_PLACEHOLDER.

**Phase 7:** `PROVIDER_CATEGORY` (serpapi/behance/dribbble → google_semantic; unsplash/pexels/pixabay/openverse → tag_based; wikimedia → catalogue; flickr → hybrid). `build_search_query(entity_name, visual_tokens, full_description, provider, strategy) -> str` — if strategy "adaptive", returns full_description for google_semantic, entity_name for catalogue, hybrid of name+tokens for hybrid, else visual_tokens. Call sites may pass book.search_query_strategy and entity.full_description to route query format per provider.

**External API:** Via provider instances: Unsplash, SerpAPI, Pexels, Pixabay, Openverse, Wikimedia, DeviantArt, Behance, Dribbble (each provider.search async). No direct HTTP in this file.

**DB:** crud.get_book, get_characters_by_book, get_locations_by_book, get_artefacts_by_book, get_cover_analysis, get_artefact, get_visual_bible, get_engine_ratings, update_character, update_location, create_search_query, create_reference_image, get_reference_image_by_entity_url, get_selected_reference_urls, trim_reference_images_fifo, get_character, get_location, get_chunks_for_character, get_chunks_for_location, get_chunk_visual_analysis, get_latest_stored_queries_for_entity.

**In-memory:** None (stateless per request).

### 4.5 ontology_service.py

**Purpose:** Classify entities (characters, locations, artefacts) into entity_class and related ontology fields via batched LLM call.

**Public functions:**

- `classify_entities_batch(entities: list[dict], entity_role: Optional[str] = None) -> list[dict]`  
  Single OpenAI call with ONTOLOGY_PROMPT (or ONTOLOGY_ARTEFACT_PROMPT when entity_role="artefact"); input [{name, description, visual_type}]; output same order with entity_class, materiality, power_status, embodiment, visual_markers, anti_human_override, search_archetype. Uses ENTITY_CLASSES or ARTEFACT_ENTITY_CLASSES from ontology_constants.

**External API:** OpenAI chat.completions (OPENAI_MODEL). **DB:** None. **In-memory:** `_client` lazy.

### 4.6 artefact_analysis_service.py (Phase 3)

**Purpose:** Extract artefacts from chunk analyses, classify via ontology, build visual tokens. Stateless; no DB.

**Public functions:**

- `extract_artefacts_from_chunks(chunk_analyses, chunk_text_map, manuscript_lang="en", run_id=None) -> list[dict]`  
  Single OpenAI call over top 30 chunks by dramatic_score; returns list of artefact dicts (name, physical_description, symbolic_role, narrative_function, typical_contexts, is_main, chunks_present, scenes_present, visual_type).

- `build_artefact_visual_tokens_batch(artefacts: list[dict]) -> list[dict]`  
  Batched LLM call for artefact-specific visual tokens; same order output with core_tokens, style_tokens, archetype_tokens, anti_tokens.

- `run_artefact_analysis(chunks, chunk_text_map, manuscript_lang="en", progress_callback=None, run_id=None) -> dict`  
  Pipeline: extract_artefacts_from_chunks → ontology_service.classify_entities_batch(entity_role="artefact") → build_artefact_visual_tokens_batch; returns { artefacts: list[dict] } with merged ontology and tokens.

**External API:** OpenAI. **DB:** None. **In-memory:** `_client` lazy.

### 4.7 cover_analysis_service.py (Phase 4)

**Purpose:** Two-stage cover design synthesis: thematic extraction then cover brief. Stateless; no DB.

**Public functions:**

- `_get_full_text_summary(chunk_analyses: list[dict]) -> str`  
  Builds summary from narrative_summary/visual_moment per chunk; caps at ~12k tokens (tiktoken).

- `extract_thematic_material(chunk_analyses, genre, run_id=None) -> dict`  
  Stage 1 LLM: returns dominant_motifs, symbolic_anchors, emotional_arc, recurring_imagery, central_tension, tone_words.

- `synthesise_cover_brief(thematic_material, genre, style_category, existing_characters, existing_locations, run_id=None) -> dict`  
  Stage 2 LLM: returns full cover_analysis-shaped dict including **Phase 7:** cover_type, color_palette_structured (dominant, accent, temperature, contrast, saturation), cover_role_primary_hint (single entity name); plus thematic_statement, emotional_promise, cover_t2i_prompt, typography_direction, color_palette_direction, cover_role_*_ids_hints as names.

- `run_cover_analysis(chunk_analyses, genre, style_category, existing_characters, existing_locations, progress_callback=None, run_id=None) -> dict`  
  Orchestrates Stage 1 → Stage 2; result ready for crud.create_or_update_cover_analysis (caller resolves cover_role_primary_hint to primary_cover_*_id).

**Constants:** GENRE_COVER_CONVENTIONS (fantasy, sci_fi, thriller, etc.). **External API:** OpenAI. **DB:** None.

### 4.8 genre_defaults.py (Phase 4)

**Purpose:** Genre-based default entity activations for analysis.

**Public:**

- `GENRE_DEFAULT_ACTIVATIONS` — dict genre → list of entity type strings (e.g. fantasy → ["cover", "characters", "locations", "artefacts"]).
- `get_default_activations(genre: str, workflow_type: str) -> list[str]`  
  For workflow_type in ("full_book", "full") returns all four; else returns GENRE_DEFAULT_ACTIVATIONS.get(genre, default).

**DB:** None.

### 4.9 scene_extractor.py

**Purpose:** Extract narrative scenes from chunk_analyses: deterministic sliding-window candidates then LLM refinement. **Phase 7:** Scene count is derived from total_words via `_auto_scene_count` (min 5, max 30, ~1 scene per 3000 words); prompt asks for min_scenes–max_scenes (no fixed count). Display limit is separate (book.scene_display_count in GET /scenes).

**Title handling:** If the LLM returns an empty or generic title (e.g. "Scene 1"), the title is derived from narrative_summary (first 5–7 words). Fallback scenes (when LLM fails or returns fewer than requested) use the first chunk's narrative_summary for the title when available.

**Public functions:**

- `_auto_scene_count(total_words: int) -> int` — One scene per ~3000 words; min 5, max 30. Used for extraction only.

- `group_chunks_into_candidate_scenes(chunk_analyses, scene_count, window_size=5, step=2) -> list[dict]`  
  Deterministic sliding window; composite score; NMS; returns top candidates.

- `extract_scenes(chunk_analyses, total_words=0, chunk_text_map, manuscript_lang, analysis_run_id=None) -> list[dict]`  
  Computes min_scenes, max_scenes from _auto_scene_count(total_words); calls group_chunks_into_candidate_scenes(max_scenes) then extract_scenes_llm(min_scenes, max_scenes); returns list of scene dicts (title, title_display, scene_type, chunk_start/end_index, narrative_summary, narrative_summary_display, visual_description, characters_present, primary_location, visual_intensity, illustration_priority, scene_prompt_draft).

- `extract_scenes_llm(candidates, min_scenes, max_scenes, chunk_text_map, manuscript_lang, analysis_run_id=None) -> list[dict]`  
  Single LLM call; prompt uses min_scenes/max_scenes (no fixed scene_count).

**External API:** OpenAI (SCENE_EXTRACTION_PROMPT). **DB:** None. **In-memory:** `_client` lazy.

### 4.10 scene_visual_composer.py

**Purpose:** Build scene_visual_tokens and t2i_prompt_json (abstract, flux, sd) per scene via batched LLM.

**Public functions:**

- `build_scene_visual_tokens(scene, character_ontologies, style_category) -> dict`  
  Single-scene wrapper; calls compose_scenes_batch([scene], ...).

- `build_t2i_prompts(scene, scene_visual_tokens, style_category) -> dict`  
  Builds abstract/flux/sd from tokens and scene_prompt_draft (no LLM).

- `compose_scenes_batch(scenes, character_ontologies, style_category) -> list[dict]`  
  Single batched OpenAI call; returns list of {scene_id, scene_visual_tokens, t2i_prompt_json}.

**External API:** OpenAI (SCENE_TOKEN_PROMPT). **DB:** None. **In-memory:** `_client` lazy.

### 4.11 engine_selector.py

**Purpose:** Select best image search providers per entity from ENGINE_AFFINITY matrix and per-book engine_ratings. Cover uses fixed COVER_PROVIDERS (behance, dribbble, unsplash, serpapi).

**Public functions:**

- `select_engines(entity_class, entity_type, style_category, available_providers, engine_ratings, top_n=2) -> list[str]`  
  When entity_type == "cover": returns COVER_PROVIDERS filtered by available_providers (no affinity matrix). Otherwise tiered fallback: exact entity_class|style_category (or entity_class only for entity_type "artefact"), parent class, generic location|human or other_artefact, then hardcoded default. Applies rating multiplier; returns up to top_n provider names from available_providers.

**Constants:** COVER_PROVIDERS = ["behance", "dribbble", "unsplash", "serpapi"].

**External API:** None. **DB:** None. **In-memory:** ENGINE_AFFINITY (includes artefact keys: physical_weapon, magical_item, etc.), ENTITY_PARENT (from ontology_constants), _DEFAULT_SCORES.

### 4.12 openverse_auth.py

**Purpose:** Openverse OAuth2: obtain and refresh access token in background.

**Public functions:**

- `fetch_token(client_id, client_secret) -> tuple[str, int]`  
  POST to Openverse token URL; returns (access_token, expires_in).

- `get_token() -> str`  
  If OPENVERSE_CLIENT_ID/SECRET set: use in-memory token or refresh; else return OPENVERSE_ACCESS_TOKEN from env.

- `start_background_refresh() -> None`  
  If client id/secret set: refresh once and start daemon thread refreshing every 9h.

**External API:** POST https://api.openverse.org/v1/auth_tokens/token/ (httpx). **DB:** None. **In-memory:** _token, _token_expires_at, _lock (threading.Lock).

### 4.13 providers/base.py

**Purpose:** Abstract base for image search providers.

**BaseImageProvider:** name (str); is_available() -> bool; search(query, content_type, count=15) -> list[dict]; format_query(raw_query) -> str (default return as-is). Returned dicts: url, thumbnail, width, height, credit, license, provider; optional search_metadata or title, description, alt, tags.

### 4.14 providers/unsplash_provider.py

**Purpose:** Unsplash API image search.

**UNSPLASH_ACCESS_KEY** from os.getenv("UNSPLASH_ACCESS_KEY", ""). is_available() = bool(access_key). search(): GET https://api.unsplash.com/search/photos, orientation portrait/landscape by content_type. Returns list of normalized dicts with search_metadata.

### 4.15 providers/serpapi_provider.py

**Purpose:** SerpAPI image search. **SERPAPI_KEY** / **SEARCH_API_KEY** from env. is_available() when key set. search() calls SerpAPI (implementation detail in file). Returns list of dicts with provider="serpapi".

### 4.16 providers/pexels_provider.py

**Purpose:** Pexels API. **PEXELS_API_KEY** from env. is_available(), search() similar pattern.

### 4.17 providers/pixabay_provider.py

**Purpose:** Pixabay API. **PIXABAY_API_KEY** from env. is_available(), search() similar pattern.

### 4.18 providers/openverse_provider.py

**Purpose:** Openverse API. Uses get_token() from openverse_auth. is_available() = True. search(): GET Openverse API with Bearer token. Returns list with provider="openverse".

### 4.19 providers/wikimedia_provider.py

**Purpose:** Wikimedia Commons API. No key. is_available() = True. User-Agent set in code. search() via commons.wikimedia.org/w/api.php.

### 4.20 providers/deviantart_provider.py

**Purpose:** DeviantArt via SerpAPI. **SERPAPI_KEY** / **SEARCH_API_KEY**. is_available(), search() delegate to SerpAPI with DeviantArt-specific params.

### 4.21 providers/behance_provider.py (Phase 6)

**Purpose:** Behance via SerpAPI Google Images with site:behance.net. **SERPAPI_KEY** / **SEARCH_API_KEY** (read in __init__ from os.getenv). is_available(), format_query (appends site:behance.net), search() returns list with provider="behance".

### 4.22 providers/dribbble_provider.py (Phase 6)

**Purpose:** Dribbble via SerpAPI Google Images with site:dribbble.com. **SERPAPI_KEY** / **SEARCH_API_KEY** (read in __init__ from os.getenv). is_available(), format_query (appends site:dribbble.com), search() returns list with provider="dribbble".

### 4.23 t2i_providers (abstract_provider, sd_provider, flux_provider)

**Purpose:** Text-to-image generation; currently stubs.

- **abstract_provider:** Stub implementation returning prompt_used without external call.
- **sd_provider:** SD_A1111_URL, SD_COMFYUI_URL from env; generate() logs and TODO; no real call.
- **flux_provider:** FAL_API_KEY, REPLICATE_API_KEY from env; generate() logs and TODO; no real call.

**DB:** None. **In-memory:** None beyond env.

---

## 5. Backend: Configuration and Environment

Full list of environment variables read in the codebase; where read; what they control; default if any. Plus .env.example / config schema.

### 5.1 Environment variables (grep: os.getenv, os.environ, get_token)

| Variable | Where read | Controls | Default |
|----------|------------|----------|---------|
| OPENAI_API_KEY | ai_service, ontology_service, scene_extractor, scene_visual_composer | OpenAI client; required for analysis/ontology/scenes | None (required) |
| OPENAI_MODEL | ai_service, ontology_service, scene_extractor, scene_visual_composer | Model name for GPT calls | "gpt-4o-mini" |
| DATABASE_URL | database.py | SQLAlchemy engine URL | "sqlite:///./app.db" |
| UNSPLASH_ACCESS_KEY | providers/unsplash_provider.py | Unsplash API | "" |
| SERPAPI_KEY | providers/serpapi_provider.py, deviantart_provider.py, behance_provider.py, dribbble_provider.py | SerpAPI, DeviantArt, Behance, Dribbble | "" |
| SEARCH_API_KEY | Same as above | Alias for SerpAPI | "" |
| PEXELS_API_KEY | providers/pexels_provider.py | Pexels API | "" |
| PIXABAY_API_KEY | providers/pixabay_provider.py | Pixabay API | "" |
| OPENVERSE_CLIENT_ID | openverse_auth.py | Openverse OAuth2 token refresh | "" |
| OPENVERSE_CLIENT_SECRET | openverse_auth.py | Openverse OAuth2 token refresh | "" |
| OPENVERSE_ACCESS_TOKEN | openverse_auth.get_token() | Openverse when no client id/secret | "" |
| SD_A1111_URL | t2i_providers/sd_provider.py | Stable Diffusion A1111 (stub) | "" |
| SD_COMFYUI_URL | t2i_providers/sd_provider.py | ComfyUI (stub) | "" |
| FAL_API_KEY | t2i_providers/flux_provider.py | FAL (stub) | "" |
| REPLICATE_API_KEY | t2i_providers/flux_provider.py | Replicate (stub) | "" |

Tests: e2e test uses SERPAPI_KEY or SEARCH_API_KEY, UNSPLASH_ACCESS_KEY to skip live provider tests if not set.

### 5.2 .env.example contents (backend/.env.example)

As in repository (abbreviated here): OPENAI_API_KEY, GEMINIGEN_API_KEY, GEMINIGEN_WEBHOOK_SECRET, UNSPLASH_ACCESS_KEY, SERPAPI_KEY, SEARCH_API_KEY, PEXELS_API_KEY, PIXABAY_API_KEY, OPENVERSE_CLIENT_ID, OPENVERSE_CLIENT_SECRET, OPENVERSE_ACCESS_TOKEN, DATABASE_URL. Comments describe each. No Pydantic settings class; all reads are os.getenv.

---

## 6. Frontend: Routing and Pages

From App.tsx (React Router).

| Path | Component | Layout | Status |
|------|-----------|--------|--------|
| / | HomePage | None | Complete |
| /settings | SettingsPage | None | Complete |
| /manuscript-upload | CreateBookPage (index) | WorkflowLayout | Complete |
| /books/:bookId | Navigate to preview | WorkflowLayout | Complete |
| /books/:bookId/manuscript-upload | CreateBookPage | WorkflowLayout | Complete |
| /books/:bookId/analysis-review | AnalysisReviewPage | WorkflowLayout | Complete |
| /books/:bookId/review-search | ReviewSearchPage | WorkflowLayout | Complete |
| /books/:bookId/review-search-result | ReviewSearchResultPage | WorkflowLayout | Complete |
| /books/:bookId/visual-bible | VisualBiblePage | WorkflowLayout | Complete |
| /books/:bookId/preview | PreviewPage (ReadingPage) | WorkflowLayout | Complete |

All routes are wrapped in AuthorWorkflowProvider (BookContext). WorkflowLayout wraps book-scoped routes and provides WorkflowNav/outlet.

---

## 7. Frontend: Component Inventory

Every component under src/components/ and src/pages/: filename, folder, props interface, API calls, context/state, key UI responsibility.

### 7.1 Components (src/components/)

**BookUpload.tsx**  
- **Props:** Typically none or callbacks (e.g. onUploadSuccess(book, metadata?), onError?).  
- **API:** POST /api/manuscripts/upload (via api or equivalent), possibly listBooks.  
- **Context/state:** useBook() for setBook, setStyleCategory, setAuthorName.  
- **UI:** File drop/select for manuscript (.txt/.docx/.pdf), title/author/words-per-page inputs, submit upload and hand off to style step.

**BookReader.tsx**  
- **Props:** Likely bookId, chunks or content, currentPage, onPageChange?.  
- **API:** getChunks(bookId) and/or getProgress/updateProgress (api.ts defines getProgress/updateProgress but backend has no /books/{id}/progress — see Stubs).  
- **Context:** useBook() if needed.  
- **UI:** Renders book text and page navigation for reading/preview.

**LoadingScreen.tsx**  
- **Props:** message?, progress? (e.g. currentChunk/totalChunks).  
- **API:** None.  
- **UI:** Full-screen loading with optional progress for analysis.

**StyleSelector.tsx**  
- **Props:** value/callbacks for style_category, illustration_frequency, layout_style, is_well_known, author, well_known_book_title, similar_book_title, scene_count; possibly mainOnlyReferences.  
- **API:** None (form only).  
- **Context:** useBook() for style fields and setSceneCount etc.  
- **UI:** Style and “well-known book” options before analyze.

**VisualBibleReview.tsx**  
- **Props:** characters, locations, artefacts?, visualBible, referenceImages, engineRatings?, onApprove(charSelections, locSelections, artefactSelections?, coverSelections?), loading?, pageTitle?, pageDescription?, bookId?, onUploadImage?, coverEntityId? (for cover uploads — book's cover_analysis id), onRefsUpdated?, onRatingUpdate?, initialTab?.  
- **API:** rateEngine(bookId, update) for like/dislike.  
- **Context:** None (props-driven).  
- **UI:** Tabs: Characters, Locations, Artefacts (if any), Cover (if referenceImages.cover has images — via getCoverImages()), Style; image grids per entity; multi-select reference URLs; approve button; optional upload and engine rating.

**WorkflowLayout.tsx**  
- **Props:** Outlet from React Router; possibly bookId from params.  
- **API:** None (or getBook for nav state).  
- **Context:** useBook().  
- **UI:** Wraps outlet with WorkflowNav and layout shell.

**WorkflowNav.tsx**  
- **Props:** Links/steps derived from route or book.  
- **API:** None.  
- **Context:** useBook() for book and navigation.  
- **UI:** Step links (preview, analysis-review, review-search, review-search-result, visual-bible, manuscript-upload).

### 7.2 Pages (src/pages/)

**HomePage.tsx**  
- **API:** listBooks(), deleteBook().  
- **Context:** useBook() setBook, navigate.  
- **UI:** List books, create new (navigate to manuscript-upload), open workflow by book, delete with confirmation.

**SetupPage.tsx (CreateBookPage)**  
- **API:** analyzeBook(bookId, params, { onProgress }), and upload (via BookUpload).  
- **Context:** useBook() for book and all style/analysis params.  
- **UI:** Steps: upload (BookUpload) → style (StyleSelector) → analyzing (LoadingScreen with progress); then navigate to analysis-review.

**AnalysisReviewPage.tsx**  
- **API:** getCharacters, getLocations, getScenes, updateEntitySelections, getBook; possibly patchEntitySummaries.  
- **Context:** useBook() for book, characters, locations, setCharacters, setLocations.  
- **UI:** Entity tables; main-entity selection (is_main); scene list; proceed to review-search.

**ReviewSearchPage.tsx**  
- **API:** getProposedSearchQueries, searchReferences, patchEntitySummaries; getProvidersStatus, getEngineRatings, rateEngine; uploadReferenceImage.  
- **Context:** useBook() for book, style, mainOnlyReferences, setReferenceImages.  
- **UI:** Edit proposed queries, run search, show results; provider toggles and engine ratings; optional reference upload.

**ReviewSearchResultPage.tsx**  
- **API:** getReferenceResults, getVisualBible; approveVisualBible; uploadReferenceImage.  
- **Context:** useBook() for book, referenceImages, setReferenceImages, setVisualBible.  
- **UI:** Review persisted reference images per entity; select multiple URLs; approve visual bible; optional upload.

**VisualBiblePage.tsx**  
- **API:** getVisualBible; approveVisualBible; uploadReferenceImage; getEngineRatings, rateEngine.  
- **Context:** useBook() for book, characters, locations, visualBible, referenceImages.  
- **UI:** Renders VisualBibleReview with data and approve/upload/rating.

**ReadingPage.tsx (PreviewPage)**  
- **API:** getChunks(bookId); getProgress/updateProgress (backend endpoints missing — see Stubs).  
- **Context:** useBook().  
- **UI:** Preview/reading view (likely BookReader).

**SettingsPage.tsx**  
- **API:** getProvidersStatus(); may use useSettings and ENABLED_PROVIDERS_STORAGE_KEY.  
- **Context:** useSettings() for localStorage model/provider choices.  
- **UI:** Provider availability toggles and optional AI/T2I model selects (localStorage only).

### 7.3 Известные пробелы (UAT Phase 1–6)

Источник: [Project Testing/UAT_Phase1-6_Conclusions_and_Recommendations.md](Project Testing/UAT_Phase1-6_Conclusions_and_Recommendations.md).

- **api.ts:** Тип `ReferenceImages` включает `characters`, `locations`, `artefacts?`, `cover?` (cover: `{ cover?: ReferenceImageItem[]; images?: ReferenceImageItem[] }` — GET reference-results возвращает `{ cover: [] }`, поиск — `{ images: [] }`). Хелпер `getCoverImages(refs)` возвращает массив обложек из любого формата. `getReferenceResults` при необходимости нормализует ответ (images → cover). `approveVisualBible` принимает character_selections, location_selections, artefact_selections?, cover_selections?. Параметр `search_entity_types` в `searchReferences` поддерживает также `artefacts`, `cover`, `all`.
- **ReviewSearchPage:** При переходе на review-search-result в state передаётся `referenceImages` с нормализованным `cover: { cover: getCoverImages(...) }`. Блоки для артефактов и обложки в proposed-search UI по-прежнему могут быть неполными; выбор «для кого искать» расширен (artefacts, cover, all).
- **ReviewSearchResultPage / VisualBiblePage:** Используют `getReferenceResults`, `getCoverImages()` для проверки наличия обложек и выбора источника данных; UI показывает секции артефактов и обложки (вкладка Cover при наличии cover images); передают artefact/cover selections при approve.
- **VisualBibleReview:** Вкладки Characters, Locations, Artefacts (если есть), Cover (если есть обложки в referenceImages — через getCoverImages), Style; `onApprove` (charSelections, locSelections, artefactSelections?, coverSelections?). Проп `coverEntityId` обязателен для отображения вкладки Cover и загрузки обложек (entity_id = cover_analysis.id).
- **SetupPage / analyzeBook:** в запрос анализа не передаётся `genre` и `entity_types` (бэкенд их принимает и сохраняет genre при analyze). Выбор workflow_type (Full / Cover only) в UI отсутствует.
- **LoadingScreen / анализ:** прогресс отображается как общий процент; данные `entity_progress` с бэкенда не показываются по типам сущностей (персонажи/локации/артефакты/обложка).
- **Повторный запуск по типу сущности:** эндпоинт `POST .../analyze/entity` есть; в UI нет кнопок/действий для перезапуска анализа по одному типу.

---

## 8. Frontend: State Management

- **React Context:** AuthorWorkflowProvider (BookContext.tsx). Value: book, characters, locations, visualBible, referenceImages, styleCategory, illustrationFrequency, layoutStyle, isWellKnown, authorName, wellKnownBookTitle, similarBookTitle, mainOnlyReferences, sceneCount, plus setters and reset(). Consumed by: HomePage, SetupPage, AnalysisReviewPage, ReviewSearchPage, ReviewSearchResultPage, VisualBiblePage, WorkflowLayout/WorkflowNav, BookUpload, StyleSelector (and any page that uses useBook()).
- **Global state:** No Zustand/Redux. Only BookContext and useSettings (localStorage).
- **localStorage:** useSettings.ts: settings_ai_model, settings_text_to_image_model, settings_reference_search_provider. api.ts: ENABLED_PROVIDERS_STORAGE_KEY = 'yread_enabled_providers' (used for enabled providers list sent to backend or for UI).

---

## 9. Backend: Current Test Coverage

**Framework:** pytest. No conftest.py in the listed tree; tests use fixtures defined in each file (e.g. module-scope client, db session).

**Test files:**

| Path | What it tests | Fixtures | Approx. cases |
|------|----------------|-----------|----------------|
| tests/unit/test_search_providers.py | Router source rewrite; provider behaviour | — | Document current behaviour (unsplash/serpapi mapping) |
| tests/unit/test_search_filter_rank.py | Filter/dedupe/rank (e.g. _filter_dedupe_and_rank, _alignment_score) | — | Multiple |
| tests/unit/test_bugs_enhancements_7_13.py | Bug/enhancement scenarios from doc | — | Several |
| tests/unit/test_query_diversification.py | Query diversification logic | — | Multiple |
| tests/unit/test_scene_visual_composer.py | Scene token/T2I composition | skip_if_unavailable (OpenAI key) | Multiple |
| tests/unit/test_entity_token_builder.py | Entity visual token builder | skip_if_unavailable | Multiple |
| tests/unit/test_provider_format_query.py | Provider format_query | Skip if “new providers” not implemented | 3 |
| tests/unit/test_scene_extractor.py | Scene extraction (group + refine) | Skip if scene_extractor not implemented | 4+ |
| tests/unit/test_engine_selector.py | select_engines tiered fallback | Skip if engine_selector not implemented | 8+ |
| tests/unit/test_ontology_service.py | classify_entities_batch | — | Multiple |
| tests/unit/test_artefact_analysis.py | Phase 3: artefact_analysis_service (extract, tokens, run_artefact_analysis, ontology entity_role, ENGINE_AFFINITY) | mocks for LLM | 7 |
| tests/unit/test_cover_analysis.py | Phase 4: cover_analysis_service and genre_defaults (_get_full_text_summary, extract_thematic_material, synthesise_cover_brief, run_cover_analysis, get_default_activations) | mocks for LLM | 8 |
| tests/unit/test_models_phase1.py | Phase 1 data model: Artefact, CoverAnalysis, VisualBibleEntry, CoverConcept, Book entity_activations, schemas | — | 7 |
| tests/unit/test_crud_phase2.py | Phase 2 CRUD: artefacts, cover_analysis, visual_bible_entries, cover_concepts, entity_activations | in-memory SQLite db fixture | 9 |
| tests/unit/test_search_phase6.py | Phase 6: Behance/Dribbble providers, select_engines cover/artefact, get_proposed_search_queries artefacts+cover, search_references_for_book artefacts | in-memory db, mock _search_all_providers | 6 |
| tests/unit/test_bugs_phase7.py | Phase 7: BUG-1/BUG-2 (entity selections, scene_display_count/show_all), cover_analysis Phase 7 fields, VB angles/entries, cover-concepts GET/POST/PATCH/select | mocks for LLM/DB | 13 |
| tests/integration/test_analysis_phase5.py | Phase 5: analyze entity_types, analysis-progress format, GET artefacts, GET/PATCH cover-analysis, entity-activations, POST analyze/entity | client_with_book (upload+chunk) | 7 |
| tests/integration/test_settings_and_analyze.py | GET /settings/providers; analyze flow with TestClient | module client, book_id from upload+chunk | 2+ |
| tests/integration/test_scene_api.py | GET/PATCH scenes; POST generate-illustration (202) | module client, book/scenes from DB | Multiple |
| tests/e2e/test_e2e_pipeline_spec.py | Full pipeline: upload → chunk → analyze → scenes → visual bible → search → T2I stub | client, book_id, fixtures | Many; some skipif no API keys; T2I and image_generation_enabled skipped |

Shared: No global conftest.py; each integration/e2e builds FastAPI TestClient and DB state as needed.

---

## 10. Frontend: Current Test Coverage

- **Test files:** No `*.test.ts`, `*.test.tsx`, `*.spec.ts`, `*.spec.tsx` found under frontend.
- **Framework:** None (no Jest/Vitest/Playwright/Cypress in package.json scripts). Frontend uses Vite, TypeScript, ESLint; no test runner configured.
- **Test utilities/mocks:** None.

---

## 11. Known Stubs and Placeholders

| Location | Type | Detail |
|----------|------|--------|
| backend/app/routers/scenes.py ~93 | Stub | POST .../scenes/{scene_id}/generate-illustration: returns 202 "Illustration generation queued (T2I provider not yet configured)"; no T2I call. |
| backend/app/routers/illustrations.py | Stub | Router empty; no endpoints. |
| backend/app/routers/webhook.py | Stub | Router empty; no endpoints. |
| backend/app/services/t2i_providers/sd_provider.py ~35–36 | Stub/TODO | generate() logs only; TODO implement A1111/ComfyUI. |
| backend/app/services/t2i_providers/flux_provider.py ~35–36 | Stub/TODO | generate() logs only; TODO implement fal/Replicate. |
| backend/app/services/t2i_providers/abstract_provider.py ~18 | Stub | Returns prompt_used without external API. |
| frontend/src/services/api.ts getProgress, updateProgress | Missing backend | Calls GET/POST `/books/${bookId}/progress`; no such routes in backend (reading_progress table dropped in migrations). |
| backend/tests/e2e/test_e2e_pipeline_spec.py ~271 | Comment | T2I is stub; assertion only 202 and message. |
| backend/tests/e2e ~294, ~324 | Skip | T2I provider not implemented; image_generation_enabled not implemented. |
| Frontend: Phase 6 artefacts/cover | Partially addressed | Cover tab on review-search-result: implemented (getCoverImages, reference-results returns cover first; VisualBibleReview receives coverEntityId; artefact/cover selections sent on approve). Remaining: proposed-search-queries UI for cover/artefacts may be minimal; reference-upload for artefact/cover is exposed. See UAT_Phase1-6_Conclusions_and_Recommendations.md. |
| Frontend: Book/create flow | Gap | genre not sent in analyze request; workflow_type (full/cover_only) has no UI control; book fields is_well_known, well_known_book_title persisted only on analyze. |
| Frontend: Analysis progress | Gap | LoadingScreen does not show per-entity progress (entity_progress from analysis-progress). |
| Frontend: Re-analyze entity | Gap | POST .../analyze/entity exists; no UI to re-trigger single entity type. |
| Backend: scene_artefacts / scene_locations | Gap | UAT reports empty scene_artefacts or few scene_locations; empty scenes (no title/summary) may be created. Logic in books.py and scene_extractor; may need verification of link_scene_artefact usage and scene filtering. |

Placeholder constants (not “stub” behaviour): CHARACTER_PLACEHOLDER, LOCATION_PLACEHOLDER in search_service and visual_bible router (URLs for default entity images). Frontend placeholder attributes (e.g. input placeholder text) are UI only.

---

## 12. Inter-Service Data Contracts

Shapes of data passed between services (where not already fully typed by Pydantic). Inferred from code.

### 12.1 ai_service.run_full_analysis → books router (persistence)

**Returns:** dict with:

- `main_characters`: list of dicts. Keys: name, physical_description, personality_traits, typical_emotions, is_main, visual_type, is_well_known_entity, canonical_search_name, search_visual_analog, ontology (dict), entity_visual_tokens (dict).
- `main_locations`: list of dicts. Keys: name, visual_description, atmosphere, is_main, is_well_known_entity, canonical_search_name, search_visual_analog, ontology, entity_visual_tokens.
- `tone_and_style`: dict. Keys: genre, mood, visual_style.
- `chunk_analyses`: list of dicts. Keys: chunk_index, visual_moment, action_level, emotional_intensity, visual_richness, illustration_priority, characters_present, locations_present, visual_layers (subject, secondary, environment, materials, lighting, mood), narrative_position, visual_density, dramatic_score, character_priority, visual_tokens (core_tokens, style_tokens, technical_tokens).
- `scenes`: list of dicts. Keys: title, title_display, scene_type, chunk_start_index, chunk_end_index, narrative_summary, narrative_summary_display, visual_description, characters_present, primary_location, visual_intensity, illustration_priority, scene_prompt_draft, scene_visual_tokens (dict), t2i_prompt_json (dict), optional _idx.
- `known_adaptations`: list[str] (when is_well_known_book).

Router maps these to crud.create_character, create_location, update_character_ontology, update_location_ontology, update_book(known_adaptations_json), create_visual_bible, chunk updates (dramatic_score, visual_analysis_json), link_chunk_characters/locations, create_scene, create_scene_character, create_scene_location.

### 12.2 search_service.search_references_for_book → visual_bible router

**Returns:** dict:

- `book_id`, `mode` ("main_only" | "all"),
- `characters`: list of { id, name, is_main, images: list[dict], placeholder_assigned: bool }. Each image dict: url, thumbnail?, width?, height?, provider (source), and optionally query_text (stripped before response).
- `locations`: same shape.
- `queries_run`: int.
- `provider_usage`: dict[str, int] (provider name → count).

Router converts to response format `characters: { name: images[] }`, `locations: { name: images[] }`, and persists to reference_images + trim_reference_images_fifo.

### 12.3 get_proposed_search_queries (search_service) → GET proposed-search-queries

**Implementation:** [backend/app/services/search_service.py](backend/app/services/search_service.py) `get_proposed_search_queries`.

**Returns:** { characters, locations, scenes, artefacts, cover? }.

- **characters:** list of { id, name, summary, visual_type?, is_well_known_entity?, canonical_search_name?, proposed_queries: list[str], text_to_image_prompt? }.
- **locations:** same shape (no visual_type).
- **scenes:** list of { id, title, title_display?, scene_type, narrative_summary, narrative_summary_display?, scene_prompt_draft, t2i_prompt_json?, illustration_priority, is_selected }.
- **artefacts:** list of entities in the same style as characters/locations: { id, name, summary, proposed_queries: list[str] } (and optionally text_to_image_prompt, etc., as in backend).
- **cover:** optional object (not a list). Present only if cover_analysis exists: `{ proposed_queries: list[str], cover_analysis_summary: str }`.

### 12.4 Provider search return shape (base.py contract)

List of dicts; each: url, thumbnail?, width?, height?, credit?, license?, provider (str). Optional: search_metadata (dict with title, description, alt, tags) or top-level title, description, alt, tags. search_service adds query_text for ranking then may strip it and search_metadata before returning to router.

### 12.5 ontology_service.classify_entities_batch

**Input:** list of { name, description, visual_type?, entity_role? }. Optional second argument: entity_role (e.g. "artefact"). When entity_role="artefact", uses ARTEFACT_ENTITY_CLASSES and ONTOLOGY_ARTEFACT_PROMPT.

**Output:** list of { name, entity_class, materiality, power_status, embodiment, visual_markers (list), anti_human_override (bool), search_archetype? } (same order).

### 12.6 Entity visual tokens (ai_service.build_entity_visual_tokens_batch)

**Input:** list of { name, description, entity_class, anti_human_override, visual_markers, search_archetype? }.

**Output:** list of { name, core_tokens, style_tokens, archetype_tokens, anti_tokens } (same order).

### 12.7 Book API (Phase 1)

**BookResponse:** Now includes entity_activations: list[str] (from JSON column), genre: str.

**BookAnalyzeRequest:** Now includes entity_types: list[str] = ["cover","characters","locations","artefacts"], genre: str = "".

**Создание книги и анализ:** При создании книги через `POST /api/manuscripts/upload` или create_book жанр и workflow_type не передаются; они обновляются при `POST /api/books/{id}/analyze` (genre, scene_count и т.д.). Фронтенд в `analyzeBook` не передаёт `genre` и `entity_types` (см. [frontend/src/services/api.ts](frontend/src/services/api.ts) и [frontend/src/pages/SetupPage.tsx](frontend/src/pages/SetupPage.tsx)).

**crud.get_selected_reference_urls:** Supports entity_type "character", "location", "artefact" (reads from respective model.selected_reference_urls); "cover" returns [].

### 12.8 artefact_analysis_service.run_artefact_analysis

**Input:** chunks (chunk_analyses list), chunk_text_map, manuscript_lang, progress_callback?, run_id?.

**Output:** { artefacts: list[dict] }. Each artefact has name, physical_description, symbolic_role, narrative_function, typical_contexts, is_main, chunks_present, scenes_present, visual_type, plus ontology fields (entity_class, visual_markers, etc.) and token fields (core_tokens, style_tokens, archetype_tokens, anti_tokens).

### 12.9 cover_analysis_service.run_cover_analysis

**Input:** chunk_analyses, genre, style_category, existing_characters, existing_locations, progress_callback?, run_id?.

**Output:** Cover brief dict: thematic_statement, emotional_promise, dominant_motifs, symbolic_anchors, cover_mood_keywords, genre_conventions, genre_subversion_opportunity, typography_direction, color_palette_direction, cover_t2i_prompt, cover_negative_prompt, cover_role_character_ids_hints, cover_role_location_ids_hints, cover_role_artefact_ids_hints (names; caller resolves to ids for crud).

### 12.10 GET analysis-progress (Phase 5) and entity activations

**GET /api/books/{book_id}/analysis-progress** response (200): `{ overall_status: "running"|"complete"|"failed", entity_progress: { entity_type: { status: "pending"|"running"|"complete"|"failed", current: int, total: int } } }`. No current_chunk/total_chunks; the frontend computes a monotonic 0–100 progress from entity_progress using dynamic phase weights (api.ts compute_overall_progress). 404 when no analysis in progress.

**PUT /api/books/{book_id}/entity-activations** body: EntityActivationsRequest (entity_activations: list[str]). Updates book.entity_activations JSON.

End of codebase snapshot. Use this document for implementation planning and test specification without ambiguity.
