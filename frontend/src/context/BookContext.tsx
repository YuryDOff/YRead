/**
 * Global state for the current book session.
 */
import { createContext, useContext, useState, type ReactNode } from 'react';
import type { Book, Character, Location, VisualBible, ReferenceImages } from '../services/api';

interface BookState {
  book: Book | null;
  characters: Character[];
  locations: Location[];
  visualBible: VisualBible | null;
  referenceImages: ReferenceImages | null;

  /* Style selections (from SetupPage before analyze) */
  styleCategory: string;
  illustrationFrequency: number;
  layoutStyle: string;
  isWellKnown: boolean;
  authorName: string;
}

interface BookContextValue extends BookState {
  setBook: (book: Book | null) => void;
  setCharacters: (chars: Character[]) => void;
  setLocations: (locs: Location[]) => void;
  setVisualBible: (vb: VisualBible | null) => void;
  setReferenceImages: (refs: ReferenceImages | null) => void;
  setStyleCategory: (s: string) => void;
  setIllustrationFrequency: (n: number) => void;
  setLayoutStyle: (s: string) => void;
  setIsWellKnown: (b: boolean) => void;
  setAuthorName: (s: string) => void;
  reset: () => void;
}

const defaults: BookState = {
  book: null,
  characters: [],
  locations: [],
  visualBible: null,
  referenceImages: null,
  styleCategory: 'fiction',
  illustrationFrequency: 4,
  layoutStyle: 'inline_classic',
  isWellKnown: false,
  authorName: '',
};

const BookContext = createContext<BookContextValue | undefined>(undefined);

export function BookProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<BookState>(defaults);

  const patch = (partial: Partial<BookState>) =>
    setState((prev) => ({ ...prev, ...partial }));

  const value: BookContextValue = {
    ...state,
    setBook: (book) => patch({ book }),
    setCharacters: (characters) => patch({ characters }),
    setLocations: (locations) => patch({ locations }),
    setVisualBible: (visualBible) => patch({ visualBible }),
    setReferenceImages: (referenceImages) => patch({ referenceImages }),
    setStyleCategory: (styleCategory) => patch({ styleCategory }),
    setIllustrationFrequency: (illustrationFrequency) => patch({ illustrationFrequency }),
    setLayoutStyle: (layoutStyle) => patch({ layoutStyle }),
    setIsWellKnown: (isWellKnown) => patch({ isWellKnown }),
    setAuthorName: (authorName) => patch({ authorName }),
    reset: () => setState(defaults),
  };

  return <BookContext.Provider value={value}>{children}</BookContext.Provider>;
}

export function useBook(): BookContextValue {
  const ctx = useContext(BookContext);
  if (!ctx) throw new Error('useBook must be used within <BookProvider>');
  return ctx;
}
