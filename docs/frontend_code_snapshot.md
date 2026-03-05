# Frontend Code Snapshot — Noctua

Снимок фронтенда для планирования, рефакторинга и интеграции с бэкендом. Точный и полный; ничего не опущено, что влияет на решения по реализации.

---

## 1. Структура проекта

```
frontend/
├── index.html
├── package.json
├── playwright.config.ts
├── vite.config.ts
├── tsconfig.json
├── tsconfig.app.json
├── tsconfig.node.json
├── eslint.config.js
├── .gitignore
├── README.md
├── e2e/
│   ├── cover_only_path.spec.ts
│   ├── full_book_path.spec.ts
│   └── fixtures/
│       ├── short_story.txt
│       └── sample_cover.jpg
└── src/
    ├── main.tsx
    ├── App.tsx
    ├── App.css
    ├── index.css
    ├── context/
    │   ├── AuthContext.tsx
    │   └── BookContext.tsx
    ├── hooks/
    │   └── useSettings.ts
    ├── services/
    │   └── api.ts
    ├── components/
    │   ├── BookUpload.tsx
    │   ├── BookReader.tsx
    │   ├── LoadingScreen.tsx
    │   ├── StyleSelector.tsx
    │   ├── VisualBibleReview.tsx
    │   ├── WorkflowLayout.tsx
    │   ├── WorkflowNav.tsx
    │   ├── FeatureGate.tsx
    │   └── CoverBriefEditor.tsx
    ├── pages/
    │   ├── HomePage.tsx
    │   ├── SetupPage.tsx          (alias: CreateBookPage)
    │   ├── AnalysisReviewPage.tsx
    │   ├── ReviewSearchPage.tsx
    │   ├── ReviewSearchResultPage.tsx
    │   ├── VisualBiblePage.tsx
    │   ├── ReadingPage.tsx        (alias: PreviewPage)
    │   ├── SettingsPage.tsx
    │   ├── MoodBoardPage.tsx
    │   ├── CoverStudioPage.tsx
    │   └── TextStudioPage.tsx
    └── tests/
        ├── setup.ts
        ├── test-wrappers.tsx
        ├── FeatureGate.test.tsx
        ├── WorkflowNav.test.tsx
        ├── AnalysisReviewPage.test.tsx
        ├── CoverBriefEditor.test.tsx
        ├── CoverStudioPage.test.tsx
        ├── MoodBoardPage.test.tsx
        ├── TextStudioPage.test.tsx
        └── …
```

---

## 2. Стек и зависимости

- **React** 19.2, **React DOM** 19.2  
- **React Router DOM** 7.13  
- **Vite** 7.2 + **@vitejs/plugin-react** 5.1  
- **TypeScript** ~5.9  
- **Tailwind CSS** 4.1.18 + **@tailwindcss/vite** 4.1.18  
- **Axios** 1.13  
- **Framer Motion** 12.33  
- **Headless UI** (@headlessui/react) 2.2  
- **Lucide React** 0.563 (иконки)

**Dev:** Vitest, @testing-library/react, @playwright/test.

Скрипты: `dev`, `build` (tsc -b && vite build), `lint`, `preview`, `test` (vitest run), `test:e2e` (playwright test).

---

## 3. Конфигурация

### 3.1 Vite (`vite.config.ts`)

- Плагины: `react()`, `tailwindcss()`.
- Прокси в dev:
  - `/api` → `http://localhost:8000` (timeout 900_000 ms).
  - `/static` → `http://localhost:8000`.
  - `/health` → `http://localhost:8000`.

### 3.2 Playwright (`playwright.config.ts`)

- `testDir: './e2e'`, `baseURL: 'http://localhost:5173'`.
- `trace: 'on-first-retry'`, `screenshot: 'only-on-failure'`.
- `webServer`: `npm run dev`, port 5173, `reuseExistingServer: !process.env.CI`.

### 3.3 API base URL (`src/services/api.ts`)

- `baseURL`: из `import.meta.env.VITE_API_URL`; если задан — приводится к виду `…/api` (без лишнего `/api` в конце).
- Если `VITE_API_URL` не задан — используется относительный `/api` (прокси в dev).

### 3.4 Стили (`src/index.css`)

- Шрифты: Playfair Display (display), Lora (body), Karla (UI).
- Цвета (Tailwind @theme): `paper-cream`, `ink-black`, `charcoal`, `sepia`, `golden`, `dusty-rose`, `sage`, `midnight`.
- Базовые стили для `html`, `body`, заголовков; классы `.page-transition-*` для анимаций.

---

## 4. Маршрутизация (`App.tsx`)

- **Providers**: `AuthProvider` (AuthContext) → `AuthorWorkflowProvider` (BookContext) → `BrowserRouter` → `Routes`.

| Путь | Элемент | Примечание |
|------|---------|------------|
| `/` | `HomePage` | Список книг, кнопка «Create Your Book Cover», удаление |
| `/settings` | `SettingsPage` | Провайдеры поиска, рейтинги движков |
| `/manuscript-upload` | `WorkflowLayout` → `CreateBookPage` (index) | Новый сценарий без bookId |
| `/books/:bookId` | `WorkflowLayout` | Вложенные маршруты ниже |
| `/books/:bookId` (index) | Redirect → `preview` | |
| `/books/:bookId/manuscript-upload` | `CreateBookPage` | Загрузка/стиль для существующей книги |
| `/books/:bookId/analysis-review` | `AnalysisReviewPage` | Табы: characters / locations / scenes / artefacts / cover; выбор главных, CoverBriefEditor (simple: только characters) |
| `/books/:bookId/mood-board` | `MoodBoardPage` | Style Reference (I2T), загрузка референса обложки, «Continue to Cover Brief» |
| `/books/:bookId/cover-brief` | `AnalysisReviewPage` | Режим Cover Brief: тип обложки, primary element, «Generate Cover» → studio/cover |
| `/books/:bookId/studio/cover` | `CoverStudioPage` | Список концептов, Regenerate, выбор, переход в Text Studio |
| `/books/:bookId/studio/text` | `TextStudioPage` | Типографика обложки (KDP) |
| `/books/:bookId/review-search` | `ReviewSearchPage` | Предложенные запросы, запуск поиска |
| `/books/:bookId/review-search-result` | `ReviewSearchResultPage` | Результаты поиска, выбор референсов, одобрение VB |
| `/books/:bookId/visual-bible` | `VisualBiblePage` | Заглушка «Next step: AI image generation» |
| `/books/:bookId/preview` | `PreviewPage` → `BookReader` | Чтение по чанкам с прогрессом |

---

## 5. Глобальное состояние

### 5.1 AuthContext (`src/context/AuthContext.tsx`)

- **Провайдер**: `AuthProvider`.
- **Хук**: `useAuth()` — возвращает `{ user, loading }`. `user` содержит `plan`: `'simple' | 'pro'` (для FeatureGate).

### 5.2 BookContext (`src/context/BookContext.tsx`)

- **Провайдер**: `AuthorWorkflowProvider`.
- **Хук**: `useBook()` — возвращает полное значение контекста; кидает, если вызван вне провайдера.

**Состояние**: `book`, `characters`, `locations`, `visualBible`, `referenceImages`; параметры стиля/анализа: `styleCategory`, `illustrationFrequency`, `layoutStyle`, `isWellKnown`, `authorName`, `wellKnownBookTitle`, `similarBookTitle`, `mainOnlyReferences`, `sceneCount`, `genre`, `workflowType`, `entityTypes`.

**Действия**: сеттеры для каждого поля + `reset()`.

**Дефолты**: `styleCategory: 'fiction'`, `illustrationFrequency: 4`, `layoutStyle: 'inline_classic'`, `entityTypes: ['cover','characters','locations','artefacts']`, остальные — по смыслу.

---

## 6. API‑клиент (`src/services/api.ts`)

- **Экземпляр**: `axios.create({ baseURL, timeout: 300_000 })`.

**Типы (экспорт)**: `Book`, `Chunk`, `Character`, `Location`, `VisualBible`, `Illustration`, `ReadingProgress`, `ReferenceImageItem`, `ReferenceImages`, `Artefact`, `ProposedEntity`, `ProposedScene`, `ProposedCover`, `ProposedSearchQueries`, `SceneResponse`, `EngineRatingUpdate/Response`, `CoverAnalysisResponse`, `CoverConceptResponse`, `I2TAnalysisResult`, `ProviderStatus`, `AnalysisProgressResponse`, и др.  
`ReferenceImageItem`: url, thumbnail?, width?, height?, source? ('unsplash'|'serpapi'|'user'|'upload'), is_selected_for_reference?.  
**Константы**: `ENABLED_PROVIDERS_STORAGE_KEY = 'noctua_enabled_providers'` (localStorage для включённых провайдеров поиска).

**Книги**: `listBooks`, `importBook`, `getBook`, `deleteBook`, `chunkBook`, `getAnalysisProgress`, `analyzeBook` (202 + polling; `scene_display_count?` в теле), `analyzeEntity`.

**Сущности**: `getCharacters`, `getLocations`, `getArtefacts`, `updateEntitySelections`, `getVisualBible`, `getProposedSearchQueries`, `patchEntitySummaries`, `searchReferences`, `getReferenceResults`, `approveVisualBible`, `uploadReferenceImage`.

**Обложка / I2T**: `getCoverAnalysis`, `analyzeCoverReference(bookId, { image_url, mode })` → `I2TAnalysisResult`; `getCoverConcepts`, `generateCoverConcepts(bookId, { concept_count?, user_instruction? })`, `selectCoverConcept(bookId, conceptId)`.

**Сцены**: `getScenes`, `updateScene`.

**Движки/настройки**: `rateEngine`, `getEngineRatings`, `getProvidersStatus`, `ENABLED_PROVIDERS_STORAGE_KEY`.

**Вспомогательные**: `getCoverImages(refs)`, `compute_overall_progress(entityProgress, requestedTypes)`.

Константы: `ANALYZE_START_TIMEOUT_MS`, `ANALYZE_POLL_INTERVAL_MS`, `ANALYZE_POLL_MAX_MS`, `PHASE_WEIGHTS`.

---

## 7. Страницы (кратко)

- **HomePage**: `listBooks`, карточки книг, кнопка «Create Your Book Cover» (navigate manuscript-upload), удаление (Headless UI Dialog).
- **SetupPage (CreateBookPage)**: шаги `upload` | `style` | `analyzing`. Upload → `BookUpload` (analysis_mode simple/pro); style → `StyleSelector`; analyzing → `LoadingScreen`. После анализа — переход на `analysis-review`. Маппинг жанра: `genreToStyleCategory`.
- **AnalysisReviewPage**: табы (characters / locations / scenes / artefacts / cover; в simple только characters). Загрузка characters, locations, scenes, artefacts, coverAnalysis; флаги is_main / is_selected_for_reference. CharacterCard: бейджи Main (иконка Star) и Secondary (иконка User); подписи на английском (Visual Data, Type, Emotions, Style tokens, Archetype, Search analog); в режиме редактирования — поля Core tokens и Style tokens (comma-separated); сохранение через `patchEntitySummaries` с `entity_visual_tokens` при редактировании токенов. Счётчик табов с атрибутом `title` (подсказка). Сохранение через `updateEntitySelections`, `updateScene`; на маршруте cover-brief рендер `CoverBriefEditor` и кнопка «Generate Cover» → navigate studio/cover.
- **MoodBoardPage**: вкладка Style Reference — загрузка референса обложки (`data-testid=cover-upload-input`), «Analyse style» (I2T), кнопка «Continue to Cover Brief». Сетка обложек: только выбранные (`is_selected_for_reference === 1` или `source === 'upload'`); после загрузки файла — тот же фильтр, при отсутствии загруженного в ответе — fallback из ответа `uploadReferenceImage`. Pro: вкладки Characters / Locations / Artefacts.
- **CoverStudioPage**: `getCoverConcepts`, polling по статусу generating; кнопка «Regenerate» → `generateCoverConcepts`; выбор концепта → `selectCoverConcept`; переход в Text Studio. `data-testid=concept-card`.
- **TextStudioPage**: типографика обложки (шрифты, цвета), экспорт под KDP.
- **ReviewSearchPage**: `getProposedSearchQueries`, редактирование запросов, `searchReferences`, переход на review-search-result.
- **ReviewSearchResultPage**: reference results, `VisualBibleReview`, `approveVisualBible`, `uploadReferenceImage`, рейтинги движков.
- **VisualBiblePage**: заглушка, «Continue to Preview».
- **ReadingPage (PreviewPage)**: при отсутствии book — `getBook(bookId)`; иначе `BookReader`.
- **SettingsPage**: `getProvidersStatus`, включение провайдеров в localStorage, рейтинги движков по книге.

---

## 8. Компоненты

- **WorkflowLayout**: по `bookId` из URL подгружает `getBook` (и при необходимости `getVisualBible`), синкает контекст; при отсутствии bookId или несовпадении id — «Loading book…»; рендер: `WorkflowNav` + `Outlet`.
- **WorkflowNav**: хлебные крошки Dashboard → этапы. Для `workflowType === 'cover_only'`: Upload, Characters, Mood Board, Cover Brief, Generate, Typography. Для full: Upload, AI Analysis, Mood Board, Cover Brief, Generate, Typography, Preview. Кнопки с `step.label`, текущий шаг по `location.pathname`.
- **BookUpload**: drag-and-drop/выбор файла; валидация .txt/.docx/.pdf, 20 MB; поля title, author, genre; радио workflow «Book Cover (Fast)» / «Full Book» (Pro); загрузка с `analysis_mode`; `onSuccess(book, metadata)`. Кнопка «Upload & Continue».
- **BookReader**: чанки через `getChunks`, пагинация, прогресс `getProgress`/`updateProgress`, навигация стрелками и клавишами.
- **StyleSelector**: стиль, частота иллюстраций, layout, well known, genre, workflowType, entityTypes, «Scenes to display»; при сабмите — контекст + `onSubmit({ sceneCount })`, кнопка «Analyze Book».
- **LoadingScreen**: режимы `analysis` | `generation`; прогресс и entity_progress; `onCancel`.
- **FeatureGate**: по `plan` (из useAuth) скрывает контент для non‑pro; используется в CoverBriefEditor (Pro-панели).
- **CoverBriefEditor**: тип обложки (`data-testid=cover-type-selector`), primary element, референс стиля; Pro: Merged Prompt, Advanced, Negative prompt (`data-testid=prompt-panel-b`). Кнопка «Generate Cover» → navigate studio/cover.
- **VisualBibleReview**: табы characters / locations / artefacts / cover / style; выбор референсов, Approve, загрузка изображений, рейтинги движков.

---

## 9. Хуки

- **useSettings** (`hooks/useSettings.ts`): localStorage (AI model, text-to-image model, reference search provider); возвращает настройки и сеттеры.
- **getPreferredSearchProvider**: `'unsplash' | 'serpapi' | undefined` для API.

---

## 10. Тесты

- **Unit**: Vitest + Testing Library; `npm run test`; файлы в `src/tests/` (FeatureGate, WorkflowNav, AnalysisReviewPage, CoverBriefEditor, CoverStudioPage, MoodBoardPage, TextStudioPage и др.); обёртки в `test-wrappers.tsx`, `setup.ts`.
- **E2E**: Playwright; `npm run test:e2e`; `e2e/cover_only_path.spec.ts` (путь upload → analysis → moodboard → cover brief → generate), `e2e/full_book_path.spec.ts` (smoke главной); фикстуры в `e2e/fixtures/`. Для полного cover-only прогона нужен бэкенд на :8000.

---

## 11. Внешние зависимости UI

- **Headless UI**: `Dialog`, `DialogPanel`, `DialogTitle`, `Menu`, `MenuButton`, `MenuItem`, `MenuItems` (HomePage, диалог удаления).
- **Framer Motion**: `motion`, `AnimatePresence` (LoadingScreen).
- **Lucide React**: иконки по всему приложению.

---

## 12. Важные детали для реализации

- При открытии книги по URL контекст заполняется в `WorkflowLayout`; при прямом заходе на preview — в `ReadingPage` через `getBook(bookId)`.
- Воркфлоу: анализ → analysis-review (выбор сущностей) → mood-board (референс обложки, I2T) → cover-brief → studio/cover (генерация) → studio/text (типографика).
- `workflowType` из контекста: `cover_only` (simple) или `full_book` (pro); задаётся при успехе загрузки из `book.analysis_mode`.
- План пользователя `user?.plan` (AuthContext) управляет FeatureGate и лимитами (например, число концептов в Cover Studio).
- Включённые провайдеры поиска: localStorage по ключу `ENABLED_PROVIDERS_STORAGE_KEY` ('noctua_enabled_providers'); настройки Review Search: `review_search_options_${bookId}`.
- Для E2E: табы с `role="tab"` и `aria-label`; обложка: `data-testid=cover-type-selector`, `data-testid=prompt-panel-b`, `data-testid=cover-upload-input`, `data-testid=concept-card`.

---

*Снимок актуален на момент обновления; при изменении маршрутов, API или контекста документ стоит обновить.*
