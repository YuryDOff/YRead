# Frontend Code Snapshot — YRead / StoryForge AI

Снимок фронтенда для планирования, рефакторинга и интеграции с бэкендом. Точный и полный; ничего не опущено, что влияет на решения по реализации.

---

## 1. Структура проекта

```
frontend/
├── index.html
├── package.json
├── vite.config.ts
├── tsconfig.json
├── tsconfig.app.json
├── tsconfig.node.json
├── eslint.config.js
├── .gitignore
├── README.md
└── src/
    ├── main.tsx
    ├── App.tsx
    ├── App.css
    ├── index.css
    ├── context/
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
    │   └── WorkflowNav.tsx
    └── pages/
        ├── HomePage.tsx
        ├── SetupPage.tsx          (alias: CreateBookPage)
        ├── AnalysisReviewPage.tsx
        ├── ReviewSearchPage.tsx
        ├── ReviewSearchResultPage.tsx
        ├── VisualBiblePage.tsx
        ├── ReadingPage.tsx        (alias: PreviewPage)
        └── SettingsPage.tsx
```

---

## 2. Стек и зависимости

- **React** 19.2, **React DOM** 19.2  
- **React Router DOM** 7.13  
- **Vite** 7.2 + **@vitejs/plugin-react** 5.1  
- **TypeScript** ~5.9  
- **Tailwind CSS** 4.1 + **@tailwindcss/vite** 4.1  
- **Axios** 1.13  
- **Framer Motion** 12.33  
- **Headless UI** (@headlessui/react) 2.2  
- **Lucide React** 0.563 (иконки)

Скрипты: `dev`, `build` (tsc -b && vite build), `lint`, `preview`.

---

## 3. Конфигурация

### 3.1 Vite (`vite.config.ts`)

- Плагины: `react()`, `tailwindcss()`.
- Прокси в dev:
  - `/api` → `http://localhost:8000` (timeout 900_000 ms).
  - `/static` → `http://localhost:8000`.
  - `/health` → `http://localhost:8000`.

### 3.2 API base URL (`src/services/api.ts`)

- `baseURL`: из `import.meta.env.VITE_API_URL`; если задан — приводится к виду `…/api` (без лишнего `/api` в конце).
- Если `VITE_API_URL` не задан — используется относительный `/api` (прокси в dev).

### 3.3 Стили (`src/index.css`)

- Шрифты: Playfair Display (display), Lora (body), Karla (UI).
- Цвета (Tailwind @theme): `paper-cream`, `ink-black`, `charcoal`, `sepia`, `golden`, `dusty-rose`, `sage`, `midnight`.
- Базовые стили для `html`, `body`, заголовков; классы `.page-transition-*` для анимаций.

---

## 4. Маршрутизация (`App.tsx`)

- **Provider**: весь приложение обёрнуто в `AuthorWorkflowProvider` (BookContext).
- **Router**: `BrowserRouter` → `Routes`.

| Путь | Элемент | Примечание |
|------|---------|------------|
| `/` | `HomePage` | Список книг, создание, удаление |
| `/settings` | `SettingsPage` | Провайдеры поиска, рейтинги движков |
| `/manuscript-upload` | `WorkflowLayout` → `CreateBookPage` (index) | Новый сценарий без bookId |
| `/books/:bookId` | `WorkflowLayout` | Вложенные маршруты ниже |
| `/books/:bookId` (index) | Redirect → `preview` | |
| `/books/:bookId/manuscript-upload` | `CreateBookPage` | Загрузка/стиль для существующей книги |
| `/books/:bookId/analysis-review` | `AnalysisReviewPage` | Выбор главных сущностей, сцены, обложка |
| `/books/:bookId/review-search` | `ReviewSearchPage` | Предложенные поисковые запросы, запуск поиска |
| `/books/:bookId/review-search-result` | `ReviewSearchResultPage` | Результаты поиска, выбор референсов, одобрение VB |
| `/books/:bookId/visual-bible` | `VisualBiblePage` | Заглушка «Next step: AI image generation» |
| `/books/:bookId/preview` | `PreviewPage` → `BookReader` | Чтение по чанкам с прогрессом |

---

## 5. Глобальное состояние: BookContext

**Файл**: `src/context/BookContext.tsx`.

- **Провайдер**: `AuthorWorkflowProvider`.
- **Хук**: `useBook()` — возвращает полное значение контекста; кидает, если вызван вне провайдера.

**Состояние**:

- `book`, `characters`, `locations`, `visualBible`, `referenceImages`.
- Параметры стиля/анализа: `styleCategory`, `illustrationFrequency`, `layoutStyle`, `isWellKnown`, `authorName`, `wellKnownBookTitle`, `similarBookTitle`, `mainOnlyReferences`, `sceneCount` (**Phase 7:** «Scenes to display» — сколько сцен показывать на Analysis Review; бэкенд извлекает по total_words отдельно), `genre`, `workflowType`, `entityTypes`.

**Действия**: сеттеры для каждого поля + `reset()` (сброс в дефолты).

**Дефолты**: `styleCategory: 'fiction'`, `illustrationFrequency: 4`, `layoutStyle: 'inline_classic'`, `entityTypes: ['cover','characters','locations','artefacts']`, остальные — пустые строки/числа/флаги по смыслу.

---

## 6. API‑клиент (`src/services/api.ts`)

- **Экземпляр**: `axios.create({ baseURL, timeout: 300_000 })`.

**Типы (экспорт)**:
- `Book`, `Chunk`, `Character`, `Location`, `VisualBible`, `Illustration`, `ReadingProgress`, `ReferenceImageItem`, `ReferenceImages`, `Artefact`, `ProposedEntity`, `ProposedScene`, `ProposedCover`, `ProposedSearchQueries`, `SceneResponse`, `EngineRatingUpdate/Response`, `CoverAnalysisResponse`, `ProviderStatus`, `AnalysisProgressResponse`, и др.

**Вспомогательные**:
- `getCoverImages(refs)` — нормализует `refs.cover` (массив / `cover` / `images`).
- `compute_overall_progress(entityProgress, requestedTypes)` — 0–100 по весам фаз (characters 60%, artefacts 20%, cover 20%).

**Книги**: `listBooks`, `importBook`, `getBook`, `deleteBook`, `chunkBook`, `getAnalysisProgress`, `analyzeBook` (202 + polling; **Phase 7:** принимает `scene_display_count?: number` в теле запроса), `analyzeEntity`.

**Сущности**: `getCharacters`, `getLocations`, `getArtefacts`, `updateEntitySelections`, `getVisualBible`, `getProposedSearchQueries`, `patchEntitySummaries`, `searchReferences`, `getReferenceResults`, `approveVisualBible`, `uploadReferenceImage`.

**Сцены**: `getScenes`, `updateScene`.

**Движки/настройки**: `rateEngine`, `getEngineRatings`, `getCoverAnalysis`, `getProvidersStatus`, `ENABLED_PROVIDERS_STORAGE_KEY`.

**Чанки/прогресс**: `getChunks`, `getProgress`, `updateProgress`.

Константы: `ANALYZE_START_TIMEOUT_MS`, `ANALYZE_POLL_INTERVAL_MS`, `ANALYZE_POLL_MAX_MS`, `PHASE_WEIGHTS`.

---

## 7. Страницы (кратко)

- **HomePage**: загрузка списка книг (`listBooks`), карточки с переходами по этапам (`WORKFLOW_STAGE_LINKS`), создание книги (navigate manuscript-upload), удаление (диалог Headless UI).
- **SetupPage (CreateBookPage)**: шаги `upload` | `style` | `analyzing`. Upload → `BookUpload`; style → `StyleSelector`; analyzing → `LoadingScreen` (mode analysis, onProgress). **Phase 7:** при запуске анализа вызывается `handleAnalyze(formValues?)`; в API передаётся `scene_display_count: formValues?.sceneCount ?? ctx.sceneCount ?? 10`. После успешного анализа — переход на `analysis-review`. Маппинг жанра в `style_category`: `genreToStyleCategory`.
- **AnalysisReviewPage**: табы characters / locations / scenes / artefacts / cover. Загрузка characters, locations, scenes, artefacts, coverAnalysis; локальные флаги is_main; сохранение через `updateEntitySelections`, `updateScene`; ре-анализ сущности через `analyzeEntity`.
- **ReviewSearchPage**: загрузка предложенных запросов (`getProposedSearchQueries`), редактирование запросов по персонажам/локациям/артефактам/обложке/сценам; опции в localStorage (`review_search_options_${bookId}`); запуск `searchReferences` с `preferred_provider` из `useSettings`; переход на `review-search-result` с `state.referenceImages` и `initialTab`.
- **ReviewSearchResultPage**: загрузка reference results, engine ratings, artefacts, cover analysis, visual bible (или characters/locations); передача в `VisualBibleReview`; одобрение VB (`approveVisualBible`), загрузка своих изображений (`uploadReferenceImage`), рейтинги движков (`rateEngine`).
- **VisualBiblePage**: заглушка с текстом и кнопкой «Continue to Preview».
- **ReadingPage (PreviewPage)**: при отсутствии book в контексте — загрузка по `bookId` из URL (`getBook`); иначе сразу `BookReader`.
- **SettingsPage**: список провайдеров (`getProvidersStatus`), включение/выключение в localStorage (`ENABLED_PROVIDERS_STORAGE_KEY`); выбор книги и отображение рейтингов движков (`getEngineRatings`).

---

## 8. Компоненты

- **WorkflowLayout**: по `bookId` из URL подгружает `getBook` и при необходимости `getVisualBible`, синкает контекст (book, style_category, illustration_frequency, layout_style); при отсутствии bookId или при несовпадении id показывает «Loading book…»; рендер: `WorkflowNav` + `Outlet`.
- **WorkflowNav**: хлебные крошки Dashboard → этапы (manuscript-upload, analysis-review, review-search, review-search-result, visual-bible, preview); ссылки вида `/books/:bookId/:segment` или `/manuscript-upload`; текущий этап по `location.pathname`.
- **BookUpload**: drag-and-drop/выбор файла; валидация типа (.txt, .docx, .pdf) и размера (20 MB); поля title, author, genre, page count; загрузка через API (POST), `onSuccess(book, metadata)` с опциональными `genre`, `author`.
- **BookReader**: чанки через `getChunks`, пагинация по ~280 слов на страницу; прогресс через `getProgress`/`updateProgress` (сохранение раз в 10 с); навигация стрелками и кнопками; клавиши ArrowLeft/ArrowRight.
- **StyleSelector**: выбор стиля (STYLES), частоты иллюстраций (2/4/8/12 страниц), layout, «well known» + опционально author, wellKnownBookTitle, similarBookTitle; genre, workflowType, entityTypes (cover, characters, locations, artefacts); **Phase 7:** блок «Scenes to display» — слайдер/инпут 3–30, описание: сколько сцен показывать на этапе Analysis Review (реальное извлечение сцен на бэкенде по объёму текста). При сабмите пишет всё в контекст и вызывает `onSubmit(formValues?)` с опциональным `formValues.sceneCount` для передачи в analyze.
- **LoadingScreen**: режимы `analysis` | `generation`; ротация сообщений; в analysis — общий прогресс и по entity_progress (если есть); `onCancel`.
- **VisualBibleReview**: табы characters / locations / artefacts / cover / style (в плане Phase 7.8 вкладка Style будет перенесена на AnalysisReviewPage и удалена отсюда). Выбор URL референсов по сущностям (charSel, locSel, artefactSel, coverSel); кнопка Approve → `onApprove(character_selections, location_selections, artefact_selections?, cover_selections?)`; опционально загрузка своего изображения (`onUploadImage`), рейтинги движков (like/dislike), `onRefsUpdated`, `onRatingUpdate`; счётчики готовности в подписях табов.

---

## 9. Хуки

- **useSettings** (`hooks/useSettings.ts`): чтение/запись в localStorage ключей AI model, text-to-image model, reference search provider; возвращает объект настроек и сеттеры.
- **getPreferredSearchProvider**: возвращает `'unsplash' | 'serpapi' | undefined` для передачи в API (например `preferred_provider`).

---

## 10. Внешние зависимости UI

- **Headless UI**: `Dialog`, `DialogPanel`, `DialogTitle`, `Menu`, `MenuButton`, `MenuItem`, `MenuItems` (HomePage — меню книги, диалог удаления).
- **Framer Motion**: `motion`, `AnimatePresence` (LoadingScreen — смена сообщений).
- **Lucide React**: иконки по всему приложению (BookOpen, ChevronRight, Loader2, User, MapPin и т.д.).

---

## 11. Важные детали для реализации

- При открытии книги по URL (`/books/:bookId/...`) контекст заполняется в `WorkflowLayout`; при прямом заходе на preview — в `ReadingPage` через `getBook(bookId)`.
- Этапы воркфлоу согласованы с бэкендом: анализ → выбор главных сущностей → предложенные запросы → поиск референсов → выбор референсов и одобрение VB → (позже) генерация иллюстраций.
- Включённые провайдеры поиска хранятся в localStorage под `ENABLED_PROVIDERS_STORAGE_KEY` и используются при поиске референсов; настройки страницы Review Search — под `review_search_options_${bookId}`.
- Типы сущностей для анализа: `cover`, `characters`, `locations`, `artefacts`; в контексте по умолчанию все четыре включены.

---

*Снимок актуален на момент создания; при изменении маршрутов, API или контекста документ стоит обновить.*
