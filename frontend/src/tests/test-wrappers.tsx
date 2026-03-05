import type { ReactNode } from 'react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { AuthorWorkflowContext } from '../context/BookContext';
import { AuthProvider } from '../context/AuthContext';
import type { Book } from '../services/api';

const defaultBookContextValue = {
  book: { id: 1, title: 'Test', author: null, analysis_mode: 'pro' } as Book,
  workflowType: 'full_book',
  characters: [],
  locations: [],
  visualBible: null,
  referenceImages: null,
  styleCategory: 'fiction',
  illustrationFrequency: 4,
  layoutStyle: 'inline_classic',
  isWellKnown: false,
  authorName: '',
  wellKnownBookTitle: '',
  similarBookTitle: '',
  mainOnlyReferences: true,
  sceneCount: 10,
  genre: '',
  entityTypes: ['cover', 'characters', 'locations', 'artefacts'],
  setBook: () => {},
  setCharacters: () => {},
  setLocations: () => {},
  setVisualBible: () => {},
  setReferenceImages: () => {},
  setStyleCategory: () => {},
  setIllustrationFrequency: () => {},
  setLayoutStyle: () => {},
  setIsWellKnown: () => {},
  setAuthorName: () => {},
  setWellKnownBookTitle: () => {},
  setSimilarBookTitle: () => {},
  setMainOnlyReferences: () => {},
  setSceneCount: () => {},
  setGenre: () => {},
  setWorkflowType: () => {},
  setEntityTypes: () => {},
  reset: () => {},
};

export function makeBookContextWrapper(opts: {
  workflowType?: 'cover_only' | 'full_book';
  book?: Book | null;
  /** Phase 12: map to book.analysis_mode for MoodBoardPage tests */
  analysisMode?: 'simple' | 'pro';
}) {
  const workflowType = opts.workflowType ?? (opts.analysisMode === 'simple' ? 'cover_only' : 'full_book');
  const analysisMode = opts.analysisMode ?? (opts.workflowType === 'cover_only' ? 'simple' : 'pro');
  const book = opts.book ?? {
    id: 1,
    title: 'Test',
    author: null,
    analysis_mode: analysisMode,
  } as Book;
  const value = {
    ...defaultBookContextValue,
    book: opts.book === null ? null : book,
    workflowType,
    setWorkflowType: () => {},
    setBook: () => {},
  };
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <AuthorWorkflowContext.Provider value={value}>
        <MemoryRouter initialEntries={['/books/1/mood-board']}>
          <Routes>
            <Route path="/books/:bookId/mood-board" element={children} />
          </Routes>
        </MemoryRouter>
      </AuthorWorkflowContext.Provider>
    );
  };
}

/** Default context for MoodBoardPage: no cover reference selected. */
export function defaultWrapper() {
  return makeBookContextWrapper({ analysisMode: 'pro', book: { id: 1, title: 'Test', author: null, analysis_mode: 'pro' } as Book });
}

/** Context with cover reference images so "Analyse style" button is visible. */
export function wrapperWithSelectedImage() {
  const refs = {
    characters: {} as Record<string, { url: string; thumbnail?: string }[]>,
    locations: {} as Record<string, { url: string; thumbnail?: string }[]>,
    cover: { cover: [{ url: '/static/ref.jpg', thumbnail: '/static/ref.jpg' }] },
  };
  const value = {
    ...defaultBookContextValue,
    book: { id: 1, title: 'Test', author: null, analysis_mode: 'pro' } as Book,
    workflowType: 'full_book' as const,
    referenceImages: refs,
    setBook: () => {},
    setReferenceImages: () => {},
  };
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <AuthorWorkflowContext.Provider value={value}>
        <MemoryRouter initialEntries={['/books/1/mood-board']}>
          <Routes>
            <Route path="/books/:bookId/mood-board" element={children} />
          </Routes>
        </MemoryRouter>
      </AuthorWorkflowContext.Provider>
    );
  };
}

/** Sets localStorage so AuthProvider picks the plan on mount. */
export function makeAuthWrapper(opts: { plan?: 'simple' | 'pro' }) {
  const plan = opts.plan ?? 'simple';
  if (typeof localStorage !== 'undefined') {
    localStorage.setItem('noctua_user_plan', plan);
  }
  return function Wrapper({ children }: { children: ReactNode }) {
    return <AuthProvider>{children}</AuthProvider>;
  };
}
