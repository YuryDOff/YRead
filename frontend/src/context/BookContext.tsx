/**
 * Global state for the author's book creation workflow.
 */
import { createContext, useContext, useState, type ReactNode } from 'react';
import type { Book, Character, Location, VisualBible, ReferenceImages } from '../services/api';

interface AuthorWorkflowState {
  book: Book | null;
  characters: Character[];
  locations: Location[];
  visualBible: VisualBible | null;
  referenceImages: ReferenceImages | null;

  /* Style selections (from CreateBookPage before analyze) */
  styleCategory: string;
  illustrationFrequency: number;
  layoutStyle: string;
  isWellKnown: boolean;
  authorName: string;
  wellKnownBookTitle: string;
  similarBookTitle: string;
  mainOnlyReferences: boolean;
  sceneCount: number;
}

interface AuthorWorkflowContextValue extends AuthorWorkflowState {
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
  setWellKnownBookTitle: (s: string) => void;
  setSimilarBookTitle: (s: string) => void;
  setMainOnlyReferences: (b: boolean) => void;
  setSceneCount: (n: number) => void;
  reset: () => void;
}

const defaults: AuthorWorkflowState = {
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
  wellKnownBookTitle: '',
  similarBookTitle: '',
  mainOnlyReferences: true,
  sceneCount: 10,
};

const AuthorWorkflowContext = createContext<AuthorWorkflowContextValue | undefined>(undefined);

export function AuthorWorkflowProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthorWorkflowState>(defaults);

  const patch = (partial: Partial<AuthorWorkflowState>) =>
    setState((prev) => ({ ...prev, ...partial }));

  const value: AuthorWorkflowContextValue = {
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
    setWellKnownBookTitle: (wellKnownBookTitle) => patch({ wellKnownBookTitle }),
    setSimilarBookTitle: (similarBookTitle) => patch({ similarBookTitle }),
    setMainOnlyReferences: (mainOnlyReferences) => patch({ mainOnlyReferences }),
    setSceneCount: (sceneCount) => patch({ sceneCount }),
    reset: () => setState(defaults),
  };

  return <AuthorWorkflowContext.Provider value={value}>{children}</AuthorWorkflowContext.Provider>;
}

export function useBook(): AuthorWorkflowContextValue {
  const ctx = useContext(AuthorWorkflowContext);
  if (!ctx) throw new Error('useBook must be used within <AuthorWorkflowProvider>');
  return ctx;
}
