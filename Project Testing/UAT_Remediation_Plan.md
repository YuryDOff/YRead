# UAT Remediation Plan — план исправлений по результатам UAT Phase 1–6

Пошаговый план исправлений по провалившимся сценариям UAT с привязкой к файлам и приоритетам.

**Ссылки:**

- Результаты UAT: таблица тестов Phase 1–6 (например, `UAT tests phase 1 to 6.xlsx` и связанные материалы).
- Выводы и рекомендации: [UAT_Phase1-6_Conclusions_and_Recommendations.md](UAT_Phase1-6_Conclusions_and_Recommendations.md).
- Снимок кодовой базы (контракты API, пробелы): [docs/codebase_snapshot.md](../docs/codebase_snapshot.md).

---

## 1. Введение

Цель документа — дать пошаговый план исправлений по провалившимся UAT-сценариям (Phase 1–6) с указанием конкретных файлов и приоритетов. После внесения изменений рекомендуется повторный прогон UAT по сценариям 1, 5, 11, 12, 13, 17–22.

---

## 2. Приоритеты и порядок

Рекомендуемый порядок работ:

1. **Фазы 1–2** — данные книги (жанр, well-known, workflow_type) и связи сцена–артефакт/локации, пустые сцены. Обеспечивает стабильные API и данные для последующих шагов.
2. **Фаза 5** — UI анализа: выборочный анализ по entity_types (сценарий 11), прогресс по сущностям (12), повторный запуск по одному типу (13).
3. **Фаза 6** — поиск и утверждение артефактов/обложки на фронтенде (сценарии 17–22).

---

## 3. Сценарий 1 (Фаза 1) — Книга: жанр, well-known, workflow_type

**Цель:** книга хранит жанр, флаги известной книги и тип рабочего процесса; фронтенд передаёт и отображает их.

- **Передавать genre при анализе и сохранять в книге:**  
  Добавить в параметры `analyzeBook` в [frontend/src/services/api.ts](../frontend/src/services/api.ts) поле `genre`; в форме (StyleSelector или SetupPage) — поле genre (из метаданных загрузки или отдельный селект). Передавать в body запроса analyze. Бэкенд уже сохраняет через `update_book(..., genre=...)` в [backend/app/routers/books.py](../backend/app/routers/books.py).

- **Проверить ответ GET /books/{id}:**  
  Убедиться, что при «известной книге» в ответе возвращаются `is_well_known`, `well_known_book_title`, `author`; при необходимости дополнить схему ответа (BookResponse) на бэкенде.

- **Добавить в UI выбор workflow_type (Full book / Cover only):**  
  Например в StyleSelector или на шаге загрузки. При создании/обновлении книги или в запросе analyze передавать и сохранять `workflow_type` (бэкенд уже поддерживает).

**Файлы:** `frontend/src/services/api.ts`, `frontend/src/pages/SetupPage.tsx`, `frontend/src/components/StyleSelector.tsx`, при необходимости схемы бэкенда (schemas.py, routers/books.py).

---

## 4. Сценарий 5 (Фаза 2) — Связи сцена–артефакт/локации, пустые сцены

**Цель:** заполненные scene_artefacts и scene_locations; отсутствие пустых сцен в основных списках.

- **Scene–artefact:**  
  Проверить в [backend/app/routers/books.py](../backend/app/routers/books.py) вызовы `link_scene_artefact` после артефакт-анализа: привязка по chunk_id/scene_id и артефактам по фрагментам. При необходимости добавить явное построение scene_artefact по правилу «артефакт в chunk → сцена содержит этот chunk».

- **Scene–locations:**  
  Проверить экстрактор сцен и сохранение scene_locations (аналогично scene_characters) в crud/создании сцен.

- **Пустые сцены:**  
  В [backend/app/services/scene_extractor.py](../backend/app/services/scene_extractor.py) (или при сохранении в router): не создавать/не сохранять сцены без title и narrative_summary или помечать их как черновик и не включать в основные списки.

**Файлы:** `backend/app/routers/books.py`, `backend/app/services/scene_extractor.py`, crud (create_scene, link_scene_*).

---

## 5. Сценарий 11 (Фаза 5) — Выборочный анализ по entity_types

**Цель:** пользователь может выбрать, какие типы сущностей анализировать (обложка, персонажи, локации, артефакты).

- В форме перед запуском анализа (StyleSelector или отдельный шаг): чекбоксы или мультиселект «Обложка», «Персонажи», «Локации», «Артефакты».
- В [frontend/src/services/api.ts](../frontend/src/services/api.ts) расширить параметры `analyzeBook`: добавить `entity_types?: string[]`.
- Передавать выбранные типы в body `POST /api/books/{id}/analyze` (бэкенд уже принимает).

**Файлы:** `frontend/src/services/api.ts`, `frontend/src/pages/SetupPage.tsx`, `frontend/src/components/StyleSelector.tsx`.

---

## 6. Сценарий 12 (Фаза 5) — Прогресс анализа по сущностям

**Цель:** экран «Анализ выполняется» показывает прогресс по каждому типу сущности.

- В [frontend/src/components/LoadingScreen.tsx](../frontend/src/components/LoadingScreen.tsx) (или экран «Анализ выполняется» в SetupPage): получать `entity_progress` из `getAnalysisProgress` и отображать по каждому типу (например, «Персонажи: 15/20», «Локации: готово», «Артефакты: в процессе», «Обложка: ожидание»).

**Файлы:** `frontend/src/components/LoadingScreen.tsx`, `frontend/src/pages/SetupPage.tsx`, `frontend/src/services/api.ts` (тип ответа analysis-progress).

---

## 7. Сценарий 13 (Фаза 5) — Повторный запуск по одному типу

**Цель:** в UI есть возможность перезапустить анализ только для одного типа сущности (персонажи, локации, артефакты, обложка).

- Добавить в api.ts функцию `analyzeEntity(bookId, entityType)`, вызывающую `POST /api/books/{id}/analyze/entity` с телом `{ entity_type }`.
- В UI (AnalysisReviewPage или карточка книги/настройки): кнопки «Перезапустить анализ: персонажи/локации/артефакты/обложка», вызывающие эту функцию.

**Файлы:** `frontend/src/services/api.ts`, `frontend/src/pages/AnalysisReviewPage.tsx` (или эквивалент).

---

## 8. Сценарии 17–22 (Фаза 6) — Артефакты и обложка на фронтенде

**Цель:** полная поддержка артефактов и обложки в потоке предложенных запросов, поиска, результатов и утверждения Visual Bible.

| Сценарий | Действия |
|----------|----------|
| **17** | В [frontend/src/pages/ReviewSearchPage.tsx](../frontend/src/pages/ReviewSearchPage.tsx): расширить тип ответа getProposedSearchQueries (artefacts, cover); отображать блоки редактирования запросов для артефактов и обложки (аналогично characters/locations). |
| **18, 19** | В api.ts: тип `search_entity_types` расширить до `'characters'|'locations'|'both'|'artefacts'|'cover'|'all'`. В ReviewSearchPage: опции «Только артефакты», «Только обложка», «Все» и передавать значение в searchReferences. |
| **20** | В api.ts: тип `ReferenceImages` расширить до `{ characters, locations, artefacts?, cover? }` (формат как в бэкенде). В ReviewSearchResultPage (и при отображении результатов): секции «Артефакты» и «Обложка». |
| **21** | В api.ts: расширить `approveVisualBible` — параметр selections включить `artefact_selections`, `cover_selections`. В VisualBibleReview: вкладки/секции для артефактов и обложки; состояние выбора и передача в onApprove. |
| **22** | Реализовать в UI вызов reference-upload для entity_type `artefact` и `cover` (entity_id для артефакта — artefact.id; для обложки — cover_analysis.id или согласованный идентификатор). Бэкенд reference-upload уже принимает entity_type artefact|cover — при необходимости проверить и задокументировать. |

**Файлы:** `frontend/src/services/api.ts`, `frontend/src/pages/ReviewSearchPage.tsx`, `frontend/src/pages/ReviewSearchResultPage.tsx`, `frontend/src/pages/VisualBiblePage.tsx`, `frontend/src/components/VisualBibleReview.tsx`.

---

## 9. Критерии приёмки и тестирование

- После внесения изменений выполнить повторный прогон UAT по сценариям **1, 5, 11, 12, 13, 17–22**.
- При необходимости обновить [docs/codebase_snapshot.md](../docs/codebase_snapshot.md) после закрытия пробелов: удалить или пометить решёнными записи в разделе 11 (Known Stubs and Placeholders).
