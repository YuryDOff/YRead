import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import AnalysisReviewPage from '../pages/AnalysisReviewPage';
import { AuthorWorkflowContext } from '../context/BookContext';
import type { Book, Character } from '../services/api';
import * as api from '../services/api';

const mockBookSimple = {
  id: 1,
  title: 'Test',
  author: null,
  analysis_mode: 'simple',
} as Book;

const mockBookPro = {
  id: 1,
  title: 'Test',
  author: null,
  analysis_mode: 'pro',
} as Book;

const mockCharacters: Character[] = [
  { id: 1, book_id: 1, name: 'Sera', physical_description: null, personality_traits: null, typical_emotions: null, reference_image_url: null, is_main: 1, is_selected_for_reference: 0 } as Character,
];

const defaultContextValue = {
  book: mockBookPro,
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
  entityTypes: [],
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

function makeBookContextWrapper(book: Book) {
  const value = { ...defaultContextValue, book };
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <AuthorWorkflowContext.Provider value={value}>
        <MemoryRouter initialEntries={[`/books/${book.id}/analysis-review`]}>
          <Routes>
            <Route path="/books/:bookId/analysis-review" element={children} />
          </Routes>
        </MemoryRouter>
      </AuthorWorkflowContext.Provider>
    );
  };
}

vi.mock('../services/api', async () => {
  const actual = await vi.importActual('../services/api');
  return {
    ...actual as object,
    getCharacters: vi.fn(() => Promise.resolve(mockCharacters)),
    getLocations: vi.fn(() => Promise.resolve([])),
    getScenes: vi.fn(() => Promise.resolve([])),
    getArtefacts: vi.fn(() => Promise.resolve([])),
    getCoverAnalysis: vi.fn(() => Promise.resolve(null)),
    updateEntitySelections: vi.fn(() => Promise.resolve({ status: 'updated', message: 'ok' })),
  };
});

describe('AnalysisReviewPage', () => {
  beforeEach(() => {
    vi.mocked(api.getCharacters).mockResolvedValue(mockCharacters);
    vi.mocked(api.getLocations).mockResolvedValue([]);
    vi.mocked(api.getScenes).mockResolvedValue([]);
    vi.mocked(api.getArtefacts).mockResolvedValue([]);
    vi.mocked(api.getCoverAnalysis).mockResolvedValue(null);
  });

  it('simple mode shows only Characters tab', async () => {
    const Wrapper = makeBookContextWrapper(mockBookSimple);
    render(
      <Wrapper>
        <AnalysisReviewPage />
      </Wrapper>
    );
    const tabBar = await screen.findByTestId('analysis-review-tabs');
    const tabButtons = tabBar.querySelectorAll('button');
    expect(tabButtons.length).toBe(1);
    expect(tabButtons[0].textContent).toMatch(/Characters/i);
  });

  it('pro mode shows all four tabs', async () => {
    const Wrapper = makeBookContextWrapper(mockBookPro);
    render(
      <Wrapper>
        <AnalysisReviewPage />
      </Wrapper>
    );
    const tabBar = await screen.findByTestId('analysis-review-tabs');
    const tabButtons = tabBar.querySelectorAll('button');
    expect(tabButtons.length).toBe(4);
    const labels = Array.from(tabButtons).map((b) => b.textContent);
    expect(labels.some((t) => t?.includes('Characters'))).toBe(true);
    expect(labels.some((t) => t?.includes('Locations'))).toBe(true);
    expect(labels.some((t) => t?.includes('Artefacts'))).toBe(true);
    expect(labels.some((t) => t?.includes('Cover'))).toBe(true);
  });

  it('is_main shown as badge, not editable', async () => {
    const Wrapper = makeBookContextWrapper(mockBookPro);
    render(
      <Wrapper>
        <AnalysisReviewPage />
      </Wrapper>
    );
    await screen.findByText('Sera');
    expect(screen.getByText('Main')).toBeInTheDocument();
    expect(screen.queryByRole('checkbox', { name: /Main character/i })).not.toBeInTheDocument();
  });

  it('is_selected_for_reference toggle calls entity-selections endpoint', async () => {
    const updateEntitySelections = vi.mocked(api.updateEntitySelections);
    const Wrapper = makeBookContextWrapper(mockBookPro);
    render(
      <Wrapper>
        <AnalysisReviewPage />
      </Wrapper>
    );
    await screen.findByText('Sera');
    const refCheckbox = screen.getByRole('checkbox', { name: /Use as reference/i });
    fireEvent.click(refCheckbox);
    const prepareBtn = screen.getByRole('button', { name: /Prepare reference search/i });
    fireEvent.click(prepareBtn);
    await waitFor(() => {
      expect(updateEntitySelections).toHaveBeenCalled();
    });
  });
});
