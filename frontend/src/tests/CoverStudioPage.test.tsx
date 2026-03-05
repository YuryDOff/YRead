import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import CoverStudioPage from '../pages/CoverStudioPage';
import { AuthorWorkflowContext } from '../context/BookContext';
import { AuthProvider } from '../context/AuthContext';
import type { Book } from '../services/api';
import * as api from '../services/api';

vi.mock('../services/api', async () => {
  const actual = await vi.importActual('../services/api');
  return {
    ...(actual as object),
    getCoverConcepts: vi.fn(() => Promise.resolve([])),
    generateCoverConcepts: vi.fn(() => Promise.resolve({ queued: 0, concepts: [] })),
    selectCoverConcept: vi.fn(() => Promise.resolve({ status: 'ok' })),
  };
});

const defaultBook = { id: 1, title: 'Test', author: null, analysis_mode: 'pro' } as Book;

function withNoConceptSelected() {
  vi.mocked(api.getCoverConcepts).mockResolvedValue([]);
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <AuthProvider>
        <AuthorWorkflowContext.Provider
          value={{
            book: defaultBook,
            setBook: () => {},
            setReferenceImages: () => {},
          } as never}
        >
          <MemoryRouter initialEntries={['/books/1/studio/cover']}>
            <Routes>
              <Route path="/books/:bookId/studio/cover" element={children} />
            </Routes>
          </MemoryRouter>
        </AuthorWorkflowContext.Provider>
      </AuthProvider>
    );
  };
}

function withConceptSelected() {
  vi.mocked(api.getCoverConcepts).mockResolvedValue([
    {
      id: 1,
      book_id: 1,
      concept_index: 1,
      status: 'complete',
      image_path: '/static/cover1.png',
      is_selected: 1,
    } as api.CoverConceptResponse,
  ]);
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <AuthProvider>
        <AuthorWorkflowContext.Provider
          value={{
            book: defaultBook,
            setBook: () => {},
            setReferenceImages: () => {},
          } as never}
        >
          <MemoryRouter initialEntries={['/books/1/studio/cover']}>
            <Routes>
              <Route path="/books/:bookId/studio/cover" element={children} />
            </Routes>
          </MemoryRouter>
        </AuthorWorkflowContext.Provider>
      </AuthProvider>
    );
  };
}

function makeAuthWrapper(plan: 'simple' | 'pro') {
  if (typeof localStorage !== 'undefined') {
    localStorage.setItem('noctua_user_plan', plan);
  }
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <AuthProvider>
        <AuthorWorkflowContext.Provider
          value={{
            book: defaultBook,
            setBook: () => {},
            setReferenceImages: () => {},
          } as never}
        >
          <MemoryRouter initialEntries={['/books/1/studio/cover']}>
            <Routes>
              <Route path="/books/:bookId/studio/cover" element={children} />
            </Routes>
          </MemoryRouter>
        </AuthorWorkflowContext.Provider>
      </AuthProvider>
    );
  };
}

describe('CoverStudioPage', () => {
  beforeEach(() => {
    vi.mocked(api.getCoverConcepts).mockResolvedValue([]);
  });

  it('shows KDP spec note above concept grid', async () => {
    render(<CoverStudioPage />, { wrapper: withNoConceptSelected() });
    expect(screen.getByText(/2560×1600/i)).toBeInTheDocument();
  });

  it('Continue button disabled until concept selected', async () => {
    render(<CoverStudioPage />, { wrapper: withNoConceptSelected() });
    const btn = screen.getByRole('button', { name: /Continue to Typography/i });
    expect(btn).toBeDisabled();
  });

  it('Continue button enabled after concept selected', async () => {
    render(<CoverStudioPage />, { wrapper: withConceptSelected() });
    const btn = await screen.findByRole('button', { name: /Continue to Typography/i });
    expect(btn).toBeEnabled();
  });

  it('Simple tier shows max 3 concept slots', async () => {
    vi.mocked(api.getCoverConcepts).mockResolvedValue([
      { id: 1, book_id: 1, concept_index: 1, status: 'complete', is_selected: 0 } as api.CoverConceptResponse,
      { id: 2, book_id: 1, concept_index: 2, status: 'complete', is_selected: 0 } as api.CoverConceptResponse,
      { id: 3, book_id: 1, concept_index: 3, status: 'complete', is_selected: 0 } as api.CoverConceptResponse,
    ]);
    render(<CoverStudioPage />, { wrapper: makeAuthWrapper('simple') });
    const slots = await screen.findAllByTestId('concept-slot');
    expect(slots.length).toBeLessThanOrEqual(3);
  });
});
