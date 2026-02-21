/**
 * User settings (models, reference search provider) stored in localStorage.
 * API keys are configured server-side via .env; this hook only stores model/provider choices.
 */

const STORAGE_KEYS = {
  AI_MODEL: 'settings_ai_model',
  TEXT_TO_IMAGE_MODEL: 'settings_text_to_image_model',
  REFERENCE_SEARCH_PROVIDER: 'settings_reference_search_provider',
} as const;

export const AI_MODEL_OPTIONS = [
  { value: 'gpt-4o-mini', label: 'OpenAI GPT-4o Mini' },
  { value: 'gpt-4o', label: 'OpenAI GPT-4o' },
  { value: 'gpt-4-turbo', label: 'OpenAI GPT-4 Turbo' },
];

export const TEXT_TO_IMAGE_MODEL_OPTIONS = [
  { value: 'leonardo', label: 'Leonardo AI' },
  { value: 'geminigen', label: 'GeminiGen' },
  { value: 'dall-e-3', label: 'OpenAI DALL-E 3' },
];

export const REFERENCE_SEARCH_PROVIDER_OPTIONS = [
  { value: '', label: 'Default (Unsplash first, then SerpAPI)' },
  { value: 'unsplash', label: 'Unsplash only' },
  { value: 'serpapi', label: 'SerpAPI only' },
];

export type ReferenceSearchProvider = 'unsplash' | 'serpapi' | '';

export interface UserSettings {
  aiModel: string;
  textToImageModel: string;
  referenceSearchProvider: ReferenceSearchProvider;
}

function getStored(key: string, defaultValue: string): string {
  if (typeof window === 'undefined') return defaultValue;
  try {
    const v = localStorage.getItem(key);
    return v !== null ? v : defaultValue;
  } catch {
    return defaultValue;
  }
}

function setStored(key: string, value: string): void {
  if (typeof window === 'undefined') return;
  try {
    localStorage.setItem(key, value);
  } catch {
    // ignore
  }
}

export function useSettings(): UserSettings & {
  setAiModel: (v: string) => void;
  setTextToImageModel: (v: string) => void;
  setReferenceSearchProvider: (v: ReferenceSearchProvider) => void;
} {
  const aiModel = getStored(STORAGE_KEYS.AI_MODEL, 'gpt-4o-mini');
  const textToImageModel = getStored(STORAGE_KEYS.TEXT_TO_IMAGE_MODEL, 'leonardo');
  const referenceSearchProvider = getStored(
    STORAGE_KEYS.REFERENCE_SEARCH_PROVIDER,
    '',
  ) as ReferenceSearchProvider;

  return {
    aiModel,
    textToImageModel,
    referenceSearchProvider: referenceSearchProvider === 'unsplash' || referenceSearchProvider === 'serpapi'
      ? referenceSearchProvider
      : '',
    setAiModel: (v: string) => setStored(STORAGE_KEYS.AI_MODEL, v),
    setTextToImageModel: (v: string) => setStored(STORAGE_KEYS.TEXT_TO_IMAGE_MODEL, v),
    setReferenceSearchProvider: (v: ReferenceSearchProvider) =>
      setStored(STORAGE_KEYS.REFERENCE_SEARCH_PROVIDER, v),
  };
}

/** For API calls: preferred_provider when user selected a specific one. */
export function getPreferredSearchProvider(): 'unsplash' | 'serpapi' | undefined {
  if (typeof window === 'undefined') return undefined;
  try {
    const v = localStorage.getItem(STORAGE_KEYS.REFERENCE_SEARCH_PROVIDER);
    if (v === 'unsplash' || v === 'serpapi') return v;
    return undefined;
  } catch {
    return undefined;
  }
}
