# Visual Pipeline Architecture: AI Analysis & Search Queries

**Назначение документа:** Единый справочник по компонентам **AI-анализа книги** и **формирования поисковых запросов** (страницы Analysis Review и Search Queries). Документ предназначен для плана рефакторинга и для онбординга разработчика, который будет менять или встраивать новый визуальный пайплайн в существующую систему.

**Вне скоупа данного пайплайна (не меняем в рамках рефакторинга этого функционала):**
- Загрузка книги (Create Book) — механика upload, chunking, создание книги.
- Презентация результатов поиска (Search Results / Review Search Result) — отображение найденных картинок, выбор референсов, approve visual bible.

**В скоупе:** всё от запуска AI-анализа после создания книги до формирования и выполнения поисковых запросов (включая предложенные запросы, правки пользователя и вызов поиска).

---

## 1. Обзор потока (High-Level Flow)

```
[Create Book — вне скоупа]
        ↓
  POST /books/{id}/chunk
        ↓
  POST /books/{id}/analyze  ←── style_category, illustration_frequency, layout_style, is_well_known, author
        ↓
  Фоновая задача: run_full_analysis → персонажи, локации, visual_bible, обогащение chunks
        ↓
  [Analysis Review] GET characters, GET locations
        ↓
  Пользователь помечает is_main, нажимает "Prepare reference search"
  PUT /books/{id}/entity-selections
        ↓
  [Search Queries] GET /books/{id}/proposed-search-queries
        ↓
  Пользователь правит summary, query lines, text_to_image_prompt
  PATCH /books/{id}/entity-summaries
  POST /books/{id}/search-references  (character_queries, location_queries, preferred_provider, search_entity_types)
        ↓
  [Search Results — вне скоупа] Review Search Result → выбор картинок → approve
```

---

## 2. Backend

### 2.1 Роль модулей

| Модуль | Назначение в пайплайне |
|--------|------------------------|
| `app/routers/books.py` | Chunk, **analyze** (POST, progress GET), characters/locations read, **entity-selections** (PUT). |
| `app/services/ai_service.py` | **run_full_analysis**: batch analysis → consolidation → post-process (dramatic_score, visual_tokens). |
| `app/services/search_service.py` | **get_proposed_search_queries**, **_build_queries**, **search_references_for_book** (Unsplash/SerpAPI). |
| `app/routers/visual_bible.py` | **proposed-search-queries** (GET), **entity-summaries** (PATCH), **search-references** (POST), reference-results (GET), approve/upload. |
| `app/crud.py` | Книги, chunks, characters, locations, visual_bible, search_queries, reference_images, chunk_characters/chunk_locations, **get_chunk_visual_analysis**, **get_chunks_for_character/location**, **get_latest_stored_queries_for_entity**. |
| `app/models.py` | Таблицы: books, chunks, characters, locations, visual_bible, search_queries, reference_images, chunk_characters, chunk_locations. |
| `app/schemas.py` | BookAnalyzeRequest, EntitySummariesUpdate, SearchReferencesRequest, CharacterResponse, LocationResponse, и др. |

### 2.2 AI Analysis (books router + ai_service)

- **Точка входа:** `POST /books/{book_id}/analyze`.
- **Тело запроса (BookAnalyzeRequest):** `style_category`, `illustration_frequency`, `layout_style`, `is_well_known`, `author`.
- **Поведение:**
  1. Проверка книги и наличия chunks.
  2. `crud.clear_analysis_results(book_id)` — удаление старых characters, locations, visual_bible, связей chunks, search_queries и т.д.
  3. Обновление книги: `author`, `is_well_known`, `status="analyzing"`.
  4. Запуск фоновой задачи `_run_analysis_background(book_id, req_dict)`.
- **Фоновая задача:**
  1. Читает chunks из БД (`chunk_index`, `text`).
  2. Вызывает `run_full_analysis(chunks, progress_callback)` из `ai_service`.
  3. В **ai_service**: батчи по 10 чанков → `analyze_chunk_batch` (GPT) → `consolidate_results` (GPT) → постобработка чанков (dramatic_score, narrative_position, visual_density, character_priority, **visual_tokens** из visual_layers).
  4. Сохраняет: characters (в т.ч. visual_type, is_well_known_entity, canonical_search_name, search_visual_analog), locations (аналогично), visual_bible (style_category из req, tone из consolidation), chunk updates (dramatic_score, visual_analysis_json с visual_layers/visual_tokens), chunk_characters, chunk_locations.
  5. В конце: `crud.update_book_status(db, book_id, "ready")`.
- **Прогресс:** in-memory `_analysis_progress[book_id]` обновляется в progress_callback; клиент опрашивает `GET /books/{book_id}/analysis-progress`.

### 2.3 Proposed Search Queries (search_service + visual_bible router)

- **Эндпоинт:** `GET /books/{book_id}/proposed-search-queries?main_only=true`.
- **Логика (get_proposed_search_queries):**
  - Берёт книгу, visual_bible (style_category), main (или все) characters и locations.
  - Для каждой сущности: если есть **сохранённые запросы** (`get_latest_stored_queries_for_entity` по entity_type + entity_name за последний «запуск» поиска, окно 15 сек), возвращает их; иначе строит запросы через **_build_queries** (см. ниже).
  - Возвращает структуру: `{ characters: [{ id, name, summary, visual_type, is_well_known_entity, canonical_search_name, proposed_queries, text_to_image_prompt }], locations: [...] }`.

### 2.4 Построение поисковых запросов (_build_queries)

Файл: `app/services/search_service.py`.

- **Входы:** entity_type (character | location), name, description, book_info (title, author, is_well_known, **style_category**), visual_tokens (core_tokens, style_tokens); для character дополнительно: visual_type, is_well_known_entity, canonical_search_name, search_visual_analog.
- **Правила:**
  - **Сукфикс:** для character — по visual_type (man/woman/animal/AI/alien/creature → " man portrait", " woman portrait" и т.д.); для location — " landscape".
  - **Well-known entity:** если is_well_known_entity и задан canonical_search_name — первым идёт запрос `{canonical_search_name}{suffix}`.
  - **Описательный запрос:** приоритет — search_visual_analog (для вымышленных), иначе core_tokens + style_tokens, иначе обрезка description + suffix.
  - **Контекст книги:** если book_info.is_well_known — добавляется запрос из title + author + ("character" для character) + "illustration".
  - К **каждому** запросу в конце добавляется **style_category** книги (из visual_bible), чтобы query_text в search_queries отражал стиль.
  - Возвращается до 3 запросов.

### 2.5 Визуальные токены для сущности (_get_visual_tokens_for_entity)

- По entity_id и entity_type находятся chunks, где сущность встречается (chunk_characters / chunk_locations).
- Для каждого такого chunk читается `visual_analysis_json` (get_chunk_visual_analysis) → извлекаются visual_tokens (core_tokens, style_tokens), дедупликация, лимиты (до 8 core, 4 style).
- Используется при построении proposed queries и при search-references, если пользователь не передал свои character_queries/location_queries.

### 2.6 Search References (POST)

- **Эндпоинт:** `POST /books/{book_id}/search-references`.
- **Тело (SearchReferencesRequest):** main_only, character_queries (entity id → list of strings), location_queries, character_summaries, location_summaries, preferred_provider ("unsplash" | "serpapi"), search_entity_types ("characters" | "locations" | "both").
- **Поведение:**
  1. При наличии character_summaries/location_summaries — сначала PATCH-подобное обновление сущностей в БД.
  2. `search_references_for_book(...)` в search_service: для каждого entity типа, включённого в search_entity_types, либо берутся user-provided queries (character_queries/location_queries), либо строятся через _build_queries. По каждому запросу — вызов Unsplash и/или SerpAPI (с учётом preferred_provider и fallback), логирование в search_queries (query_text, results_count, provider). Результаты фильтруются и дедуплицируются (_filter_and_dedupe), до 15 изображений на сущность.
  3. В visual_bible router ответ переводится в формат `{ characters: { name: images[] }, locations: { name: images[] } }`, затем все найденные изображения сохраняются в **reference_images** (append), для каждой сущности вызывается FIFO trim (лимит 50 на сущность, выбранные пользователем не удаляются).

### 2.7 Entity Summaries (PATCH)

- **Эндпоинт:** `PATCH /books/{book_id}/entity-summaries`.
- **Тело (EntitySummariesUpdate):** characters: [{ id, physical_description?, text_to_image_prompt?, visual_type?, ... }], locations: [{ id, visual_description?, text_to_image_prompt?, ... }].
- Обновляет переданные поля в characters и locations (по id). Вызывается с фронта перед «Run reference search», чтобы сохранить правки summary и text_to_image_prompt.

### 2.8 Остальные эндпоинты, затрагивающие пайплайн

- `GET /books/{book_id}/characters` — список персонажей (для Analysis Review).
- `GET /books/{book_id}/locations` — список локаций (для Analysis Review).
- `PUT /books/{book_id}/entity-selections` — массовое обновление is_main (characters/locations). Тело: EntitySelectionsRequest (characters: [{ id, is_main }], locations: [{ id, is_main }]).
- `GET /books/{book_id}/reference-results` — persisted reference images по сущностям (для Review Search Result; в скоупе пайплайна можно не менять).
- `GET /books/{book_id}/search-queries` — лог поисковых запросов по книге (аудит).

---

## 3. Frontend

### 3.1 Маршруты и layout

- Роуты в `App.tsx`: под `WorkflowLayout` (с WorkflowNav):
  - `/books/:bookId/analysis-review` → AnalysisReviewPage
  - `/books/:bookId/review-search` → ReviewSearchPage
- WorkflowNav показывает этапы: Create Book → Analysis Review → Search Queries → Search Results → Visual Bible → Preview. Текущий этап и переход по книге через `bookId` в URL (чтобы при refresh оставаться на том же шаге).

### 3.2 Analysis Review Page

- **Файл:** `frontend/src/pages/AnalysisReviewPage.tsx`.
- **Данные:** при монтировании — `getCharacters(bookId)`, `getLocations(bookId)`. Локальный state: charMainFlags, locMainFlags (id → boolean), инициализируются из is_main.
- **UI:** списки персонажей и локаций с возможностью переключения «звёздочки» (is_main). Кнопка «Prepare reference search» сохраняет выбранные is_main через `updateEntitySelections(bookId, { characters, locations })` и переходит на `/books/:bookId/review-search`.
- **Контекст:** useBook() — book, setReferenceImages не используется на этой странице.

### 3.3 Review Search Page (Search Queries)

- **Файл:** `frontend/src/pages/ReviewSearchPage.tsx`.
- **Данные:** при монтировании — `getProposedSearchQueries(bookId, true)`. Результат кладётся в state: characters/locations с полями id, name, summary, proposed_queries → отображаются как редактируемые списки строк `queries`, плюс text_to_image_prompt.
- **Важно:** при открытии страницы должны показываться **актуальные** данные из БД: последние сохранённые запросы возвращаются через proposed-search-queries (бэкенд использует get_latest_stored_queries_for_entity при наличии прошлого поиска). Если после правок и поиска пользователь вернётся на страницу — ожидается показ последних запросов из БД (известный баг в «Bugs and enhancements»: после навигации туда-обратно показывались старые запросы — при рефакторинге убедиться, что бэкенд и фронт всегда опираются на последние сохранённые данные).
- **Опции поиска:** Search engine (Default / Unsplash / SerpAPI), Search for (Characters only / Locations only / Both). Сохраняются в localStorage по ключу `review_search_options_${bookId}` и восстанавливаются при открытии. Для «Search for» допустимые значения зависят от наличия только персонажей, только локаций или обоих.
- **Run reference search:**
  1. `patchEntitySummaries(bookId, { characters, locations })` — сохраняются summary и text_to_image_prompt.
  2. `searchReferences(bookId, true, { character_queries, location_queries, preferred_provider, search_entity_types })` — запросы передаются для **всех** сущностей на странице (бэкенд использует только их, без fallback на автозапросы).
  3. Результат записывается в ctx.setReferenceImages; редирект на `/books/:bookId/review-search-result` с state.initialTab (characters или locations в зависимости от search_entity_types).

### 3.4 API (frontend/src/services/api.ts)

- **Анализ:** `analyzeBook(bookId, { style_category, illustration_frequency, layout_style, is_well_known, author }, { onProgress })` — POST analyze, затем опрос getBook + getAnalysisProgress до status ready/error.
- **Сущности:** getCharacters, getLocations, updateEntitySelections.
- **Proposed / Search:** getProposedSearchQueries(bookId, mainOnly), patchEntitySummaries(bookId, body), searchReferences(bookId, mainOnly, body).
- Типы: ProposedEntity (id, name, summary, visual_type, is_well_known_entity, canonical_search_name, proposed_queries, text_to_image_prompt), ReferenceImages (characters/locations — name → array of { url, thumbnail, width, height, source }).

### 3.5 Контекст (BookContext)

- Хранит: book, characters, locations, visualBible, referenceImages, styleCategory, illustrationFrequency, layoutStyle, isWellKnown, authorName, mainOnlyReferences.
- Create Book (SetupPage) перед анализом использует styleCategory и др.; после успешного analyzeBook выполняется переход на analysis-review. Стиль книги (style_category) должен сохраняться и отображаться на create-book при возврате (отдельный баг в «Bugs and enhancements»: стиль не сохранялся).

---

## 4. Database Schema (релевантные таблицы)

- **books:** id, title, author, file_path, total_words, total_pages, status (imported | chunked | analyzing | ready | error), is_well_known, workflow_type, is_well_known_book, similar_book_title, created_at, updated_at.
- **chunks:** id, book_id, chunk_index, text, start_page, end_page, word_count, dramatic_score, **visual_analysis_json** (JSON: visual_layers, visual_tokens).
- **characters:** id, book_id, name, physical_description, personality_traits, typical_emotions, reference_image_url, selected_reference_urls (JSON), is_main, **visual_type**, **is_well_known_entity**, **canonical_search_name**, **search_visual_analog**, **text_to_image_prompt**.
- **locations:** id, book_id, name, visual_description, atmosphere, reference_image_url, selected_reference_urls (JSON), is_main, **is_well_known_entity**, **canonical_search_name**, **search_visual_analog**, **text_to_image_prompt**.
- **visual_bible:** id, book_id, **style_category**, tone_description, illustration_frequency, layout_style, approved_at.
- **search_queries:** id, book_id, entity_type, entity_name, **query_text**, results_count, provider, created_at.
- **reference_images:** id, book_id, entity_type, entity_id, url, thumbnail, width, height, source (unsplash | serpapi | user), created_at. FIFO cap 50 на (entity_type, entity_id), выбранные пользователем не удаляются при trim.
- **chunk_characters:** chunk_id, character_id (связь чанк–персонаж для агрегации visual tokens по сущности).
- **chunk_locations:** chunk_id, location_id.

---

## 5. Концептуальный дизайн: от визуальных слоёв к запросам

### 5.1 Цепочка данных (концепт из старого visual_pipeline_architecture)

- **Visual layers** (из AI по чанкам): subject, secondary, environment, materials, lighting, mood, style, camera.
- **Normalizer:** абстрактные термины (sacred, dystopian, minimalism, divine) → визуальные маркеры (см. примеры в оригинальном документе).
- **Token builder:** из слоёв формируются core_tokens, style_tokens, technical_tokens. В текущем коде это делается в ai_service.build_visual_tokens(visual_layers) и сохраняется в chunk_analysis.visual_tokens.
- **Search query builder:** из токенов (и полей сущности) строится строка для SERP/Unsplash — в search_service._build_queries; в query_text **не** входит имя сущности (только визуальные дескрипторы + опционально canonical name для well-known).
- **Text-to-image prompt:** отдельное поле text_to_image_prompt на character/location; пользователь редактирует на Review Search; для генерации иллюстраций не входит в текущий документ (вне скоупа поиска).

### 5.2 Правила поисковых запросов (требования из requirements)

- В query_text только визуальные термины (и при необходимости canonical_search_name). Имя персонажа/локации в запрос не подставлять, чтобы не сужать выдачу.
- Стиль книги (style_category с create-book) должен входить в запросы и сохраняться в search_queries.query_text.
- Выбор провайдера (Unsplash / SerpAPI) и тип сущностей (characters / locations / both) задаётся пользователем на Review Search и передаётся в POST search-references.

---

## 6. API Reference (только эндпоинты пайплайна Analysis + Search Queries)

| Method | Path | Назначение |
|--------|------|------------|
| POST | /books/{id}/chunk | Разбить книгу на чанки (нужно до анализа). |
| POST | /books/{id}/analyze | Запуск AI-анализа (202, фон). Body: style_category, illustration_frequency, layout_style, is_well_known, author. |
| GET | /books/{id}/analysis-progress | Прогресс анализа (current_chunk, total_chunks). 404 если анализ не идёт. |
| GET | /books/{id}/characters | Список персонажей (для Analysis Review). |
| GET | /books/{id}/locations | Список локаций (для Analysis Review). |
| PUT | /books/{id}/entity-selections | Обновить is_main у characters и locations. Body: characters: [{ id, is_main }], locations: [{ id, is_main }]. |
| GET | /books/{id}/proposed-search-queries | Предложенные запросы и text_to_image_prompt по main (или всем) сущностям. ?main_only=true. |
| PATCH | /books/{id}/entity-summaries | Обновить physical_description, visual_description, text_to_image_prompt и др. Body: characters[], locations[]. |
| POST | /books/{id}/search-references | Выполнить поиск референсов. Body: main_only, character_queries, location_queries, preferred_provider, search_entity_types. |
| GET | /books/{id}/search-queries | Лог поисковых запросов (аудит). |

---

## 7. Известные проблемы и пожелания (из Bugs and enhancements)

- На Review Search после навигации должны показываться **последние** сохранённые запросы/summary/text_to_image_prompt из БД (не старые с предыдущего открытия).
- Refresh страницы не должен сбрасывать пользователя на Home — используется bookId в URL и восстановление книги по нему (при рефакторинге проверить восстановление контекста).
- Стиль книги на create-book должен сохраняться и отображаться при возврате; список стилей расширить (например Sci-fi, Cyberpunk, space opera).
- Выбранный стиль книги должен входить в reference image search query string (уже реализовано через style_category в _build_queries; при рефакторинге не терять).
- Для хорошо известных опубликованных книг: учитывать не только саммари книги, но и сюжет из внешних источников (Wikipedia/LLM) при формировании контекста (возможное расширение пайплайна).

---

## 8. Точки интеграции для нового визуального пайплайна

- **Вход:** после chunk и перед/вместо текущего `POST /books/{id}/analyze`. Либо замена ai_service.run_full_analysis на новую реализацию, либо дополнительный шаг (например, обогащение визуальных слоёв/токенов).
- **Выход анализа:** те же таблицы (characters, locations, visual_bible, chunks.visual_analysis_json, chunk_characters, chunk_locations). Сохранение формата visual_tokens (core_tokens, style_tokens) позволит не менять search_service.
- **Proposed queries:** GET proposed-search-queries и _build_queries должны получать все нужные поля (style_category, visual_type, is_well_known_entity, canonical_search_name, search_visual_analog) из БД; при смене формата анализа нужно обновить только источник этих полей и при необходимости формат visual_tokens.
- **Search:** POST search-references и провайдеры (Unsplash/SerpAPI) можно оставить; при рефакторинге можно вынести построение запросов в отдельный сервис/модуль и подменить алгоритм (например, другой нормалайзер или веса токенов).
- **Frontend:** Analysis Review и Review Search остаются точками ввода; при изменении структуры proposed_queries или entity-summaries нужно обновить типы и формы на фронте.

---

## 9. Краткий чеклист для рефакторинга

- [ ] Документировать контракты API (request/response) для analyze, proposed-search-queries, entity-summaries, search-references.
- [ ] Обеспечить загрузку последних сохранённых запросов и summary при открытии Review Search (бэкенд + фронт).
- [ ] Сохранение и отображение style_category (и списка стилей) на Create Book и передача в анализ и в запросы.
- [ ] При замене пайплайна: сохранить или явно мигрировать формат visual_analysis_json (visual_layers, visual_tokens) и поля сущностей (visual_type, search_visual_analog и т.д.).
- [ ] Тесты: построение запросов (well-known, fictional, с style_category); предложенные запросы после первого и повторного поиска; полный цикл analyze → entity-selections → entity-summaries → search-references.
