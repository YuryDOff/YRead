import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import TextStudioPage from '../pages/TextStudioPage';
import { AuthorWorkflowContext } from '../context/BookContext';
import { AuthProvider } from '../context/AuthContext';
import type { Book } from '../services/api';

const defaultBook = { id: 1, title: 'Test Book', author: 'Author', analysis_mode: 'pro' } as Book;

function Wrapper({ children }: { children: React.ReactNode }) {
  return (
    <AuthProvider>
      <AuthorWorkflowContext.Provider
        value={{
          book: defaultBook,
          setBook: () => {},
          setReferenceImages: () => {},
        } as never}
      >
        <MemoryRouter initialEntries={['/books/1/studio/text']}>
          <Routes>
            <Route path="/books/:bookId/studio/text" element={children} />
          </Routes>
        </MemoryRouter>
      </AuthorWorkflowContext.Provider>
    </AuthProvider>
  );
}

describe('TextStudioPage', () => {
  it('renders canvas element', () => {
    render(<TextStudioPage />, { wrapper: Wrapper });
    expect(document.querySelector('canvas')).toBeInTheDocument();
  });

  it('export button shows KDP spec', () => {
    render(<TextStudioPage />, { wrapper: Wrapper });
    expect(screen.getByRole('button', { name: /KDP compatible/i })).toBeInTheDocument();
  });

  it('custom font upload gated behind FeatureGate', () => {
    render(<TextStudioPage />, { wrapper: Wrapper });
    expect(screen.queryByText(/Upload custom font/i)).not.toBeInTheDocument();
  });
});
