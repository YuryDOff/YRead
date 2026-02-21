/**
 * API client for the Reading Reinvented backend.
 */
import axios from 'axios';

// Base URL for API: if VITE_API_URL is set, use it and ensure it ends with /api
const envBase = import.meta.env.VITE_API_URL || '';
const baseURL = envBase
  ? (envBase.endsWith('/api') ? envBase : envBase.replace(/\/$/, '') + '/api')
  : '/api';

export const api = axios.create({
  baseURL,
  timeout: 300_000, // 5 min – analysis can be slow
});

/* ------------------------------------------------------------------ */
/* Types                                                               */
/* ------------------------------------------------------------------ */

export interface Book {
  id: number;
  title: string;
  author: string | null;
  google_drive_link: string | null;
  total_words: number | null;
  total_pages: number | null;
  status: string | null;
  is_well_known: number;
  well_known_book_title?: string | null;
  similar_book_title?: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface Chunk {
  id: number;
  book_id: number;
  chunk_index: number;
  text: string;
  start_page: number | null;
  end_page: number | null;
  word_count: number | null;
  dramatic_score: number | null;
}

export interface Character {
  id: number;
  book_id: number;
  name: string;
  physical_description: string | null;
  personality_traits: string | null;
  typical_emotions: string | null;
  reference_image_url: string | null;
  selected_reference_urls?: string[];
  is_main: number;
}

export interface Location {
  id: number;
  book_id: number;
  name: string;
  visual_description: string | null;
  atmosphere: string | null;
  reference_image_url: string | null;
  selected_reference_urls?: string[];
  is_main: number;
}

export interface VisualBible {
  id: number;
  book_id: number;
  style_category: string | null;
  tone_description: string | null;
  illustration_frequency: number | null;
  layout_style: string | null;
  approved_at: string | null;
}

export interface Illustration {
  id: number;
  book_id: number;
  chunk_id: number | null;
  page_number: number | null;
  image_path: string | null;
  prompt: string | null;
  style: string | null;
  status: string | null;
  created_at: string | null;
}

export interface ReadingProgress {
  id: number;
  book_id: number;
  current_page: number;
  last_read_at: string | null;
}

export interface ReferenceImageItem {
  url: string;
  thumbnail?: string;
  width?: number;
  height?: number;
  source?: 'unsplash' | 'serpapi' | 'user';
}

export interface ReferenceImages {
  characters: Record<string, ReferenceImageItem[]>;
  locations: Record<string, ReferenceImageItem[]>;
}

/* ------------------------------------------------------------------ */
/* Book endpoints                                                      */
/* ------------------------------------------------------------------ */

export async function listBooks(): Promise<Book[]> {
  const { data } = await api.get<Book[]>('/books');
  return Array.isArray(data) ? data : [];
}

export async function importBook(googleDriveLink: string): Promise<Book> {
  const { data } = await api.post<Book>('/books/import', {
    google_drive_link: googleDriveLink,
  });
  return data;
}

export async function getBook(bookId: number): Promise<Book> {
  const { data } = await api.get<Book>(`/books/${bookId}`);
  return data;
}

export async function getAnalysisProgress(
  bookId: number,
): Promise<{ current_chunk: number; total_chunks: number } | null> {
  try {
    const { data } = await api.get<{ current_chunk: number; total_chunks: number }>(
      `/books/${bookId}/analysis-progress`,
    );
    return data;
  } catch {
    return null;
  }
}

export async function deleteBook(bookId: number): Promise<void> {
  await api.delete(`/books/${bookId}`);
}

export async function chunkBook(bookId: number): Promise<{ status: string; message: string }> {
  const { data } = await api.post(`/books/${bookId}/chunk`);
  return data;
}

/** Start analysis returns 202; we poll book status until ready/error. */
const ANALYZE_START_TIMEOUT_MS = 30_000; // only wait for 202
const ANALYZE_POLL_INTERVAL_MS = 4000;
const ANALYZE_POLL_MAX_MS = 900_000; // 15 min max polling

export async function analyzeBook(
  bookId: number,
  params: {
    style_category: string;
    illustration_frequency: number;
    layout_style: string;
    is_well_known: boolean;
    author?: string;
    well_known_book_title?: string;
    similar_book_title?: string;
    scene_count?: number;
  },
  options?: { onProgress?: (currentChunk: number, totalChunks: number) => void },
): Promise<{ status: string; estimated_time: number }> {
  await api.post(`/books/${bookId}/analyze`, params, {
    timeout: ANALYZE_START_TIMEOUT_MS,
    validateStatus: (s) => s === 202 || s === 200,
  });
  const deadline = Date.now() + ANALYZE_POLL_MAX_MS;
  while (Date.now() < deadline) {
    const [book, progress] = await Promise.all([
      getBook(bookId),
      getAnalysisProgress(bookId),
    ]);
    const status = book.status ?? '';
    if (status === 'ready') {
      return { status: 'ready', estimated_time: 0 };
    }
    if (status === 'error') {
      throw new Error('Analysis failed. Please try again.');
    }
    if (progress && options?.onProgress) {
      options.onProgress(progress.current_chunk, progress.total_chunks);
    }
    await new Promise((r) => setTimeout(r, ANALYZE_POLL_INTERVAL_MS));
  }
  throw new Error('Analysis is taking longer than expected. Check back later.');
}

/* ------------------------------------------------------------------ */
/* Characters / Locations                                              */
/* ------------------------------------------------------------------ */

export async function getCharacters(bookId: number): Promise<Character[]> {
  const { data } = await api.get<Character[]>(`/books/${bookId}/characters`);
  return data;
}

export async function getLocations(bookId: number): Promise<Location[]> {
  const { data } = await api.get<Location[]>(`/books/${bookId}/locations`);
  return data;
}

export async function updateEntitySelections(
  bookId: number,
  selections: {
    characters: { id: number; is_main: boolean }[];
    locations: { id: number; is_main: boolean }[];
  },
): Promise<{ status: string; message: string }> {
  const { data } = await api.put(`/books/${bookId}/entity-selections`, selections);
  return data;
}

/* ------------------------------------------------------------------ */
/* Visual Bible                                                        */
/* ------------------------------------------------------------------ */

export async function getVisualBible(bookId: number) {
  const { data } = await api.get<{
    visual_bible: VisualBible;
    characters: Character[];
    locations: Location[];
  }>(`/books/${bookId}/visual-bible`);
  return data;
}

export interface ProposedEntity {
  id: number;
  name: string;
  summary: string;
  visual_type?: string | null;
  is_well_known_entity?: boolean;
  canonical_search_name?: string | null;
  proposed_queries: string[];
  text_to_image_prompt?: string;
}

export interface SceneResponse {
  id: number;
  book_id: number;
  title: string | null;
  title_display?: string | null;  // manuscript language for UI
  scene_type: string | null;
  chunk_start_index: number;
  chunk_end_index: number;
  narrative_summary: string | null;
  narrative_summary_display?: string | null;  // manuscript language for UI
  visual_description: string | null;
  scene_prompt_draft: string | null;
  t2i_prompt_json: { abstract?: string; flux?: string; sd?: string } | null;
  scene_visual_tokens: Record<string, unknown> | null;
  dramatic_score_avg: number | null;
  illustration_priority: string | null;
  narrative_position: string | null;
  is_selected: boolean;
  characters_present: string[];
  primary_location: string | null;
}

export interface EngineRatingUpdate {
  provider: string;
  action: 'like' | 'dislike';
}

export interface EngineRatingResponse {
  provider: string;
  likes: number;
  dislikes: number;
  net_score: number;
}

export interface ProposedScene {
  id: number;
  title: string | null;
  title_display?: string | null;  // manuscript language for UI
  scene_type: string | null;
  narrative_summary: string | null;
  narrative_summary_display?: string | null;  // manuscript language for UI
  scene_prompt_draft: string | null;
  t2i_prompt_json: { abstract?: string; flux?: string; sd?: string } | null;
  illustration_priority: string | null;
  is_selected: boolean;
}

export interface ProposedSearchQueries {
  characters: ProposedEntity[];
  locations: ProposedEntity[];
  scenes?: ProposedScene[];
}

export async function getProposedSearchQueries(
  bookId: number,
  mainOnly: boolean = true,
): Promise<ProposedSearchQueries> {
  const { data } = await api.get<ProposedSearchQueries>(
    `/books/${bookId}/proposed-search-queries`,
    { params: { main_only: mainOnly } },
  );
  return data;
}

export async function patchEntitySummaries(
  bookId: number,
  body: { characters: Record<string, unknown>[]; locations: Record<string, unknown>[] },
) {
  await api.patch(`/books/${bookId}/entity-summaries`, body);
}

export async function searchReferences(
  bookId: number,
  mainOnly: boolean = true,
  body?: {
    character_queries?: Record<string, string[]>;
    location_queries?: Record<string, string[]>;
    character_summaries?: Record<string, Record<string, unknown>>;
    location_summaries?: Record<string, Record<string, unknown>>;
    preferred_provider?: 'unsplash' | 'serpapi';
    search_entity_types?: 'characters' | 'locations' | 'both';
    enabled_providers?: string[];
  },
): Promise<ReferenceImages> {
  const { data } = await api.post<ReferenceImages>(
    `/books/${bookId}/search-references`,
    { main_only: mainOnly, ...body },
  );
  return data;
}

export async function getReferenceResults(bookId: number): Promise<ReferenceImages> {
  const { data } = await api.get<ReferenceImages>(`/books/${bookId}/reference-results`);
  return data;
}

export async function approveVisualBible(
  bookId: number,
  selections: {
    character_selections: Record<string, string[]>;
    location_selections: Record<string, string[]>;
  },
) {
  const { data } = await api.post(`/books/${bookId}/visual-bible/approve`, selections);
  return data;
}

/* ------------------------------------------------------------------ */
/* Scenes                                                              */
/* ------------------------------------------------------------------ */

export async function getScenes(bookId: number): Promise<SceneResponse[]> {
  const { data } = await api.get<SceneResponse[]>(`/books/${bookId}/scenes`);
  return data;
}

export async function updateScene(
  bookId: number,
  sceneId: number,
  updates: { title?: string; scene_prompt_draft?: string; is_selected?: boolean },
): Promise<SceneResponse> {
  const { data } = await api.patch<SceneResponse>(
    `/books/${bookId}/scenes/${sceneId}`,
    updates,
  );
  return data;
}

/* ------------------------------------------------------------------ */
/* Engine Ratings                                                      */
/* ------------------------------------------------------------------ */

export async function rateEngine(
  bookId: number,
  update: EngineRatingUpdate,
): Promise<void> {
  await api.patch(`/books/${bookId}/engine-ratings`, update);
}

export async function getEngineRatings(bookId: number): Promise<EngineRatingResponse[]> {
  const { data } = await api.get<EngineRatingResponse[]>(`/books/${bookId}/engine-ratings`);
  return data;
}

export const ENABLED_PROVIDERS_STORAGE_KEY = 'yread_enabled_providers';

export interface ProviderStatus {
  name: string;
  label: string;
  available: boolean;
}

export async function getProvidersStatus(): Promise<ProviderStatus[]> {
  const { data } = await api.get<{ providers: ProviderStatus[] }>('/settings/providers');
  return data.providers ?? [];
}

export async function uploadReferenceImage(
  bookId: number,
  entityType: 'character' | 'location',
  entityId: number,
  file: File,
): Promise<ReferenceImageItem & { id?: number }> {
  const form = new FormData();
  form.append('entity_type', entityType);
  form.append('entity_id', String(entityId));
  form.append('file', file);
  const { data } = await api.post(`/books/${bookId}/reference-upload`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

/* ------------------------------------------------------------------ */
/* Chunks                                                              */
/* ------------------------------------------------------------------ */

export async function getChunks(bookId: number): Promise<Chunk[]> {
  const { data } = await api.get<Chunk[]>(`/books/${bookId}/chunks`);
  return data;
}

/* ------------------------------------------------------------------ */
/* Reading Progress                                                    */
/* ------------------------------------------------------------------ */

export async function getProgress(bookId: number): Promise<ReadingProgress> {
  const { data } = await api.get<ReadingProgress>(`/books/${bookId}/progress`);
  return data;
}

export async function updateProgress(bookId: number, currentPage: number) {
  const { data } = await api.post(`/books/${bookId}/progress`, {
    current_page: currentPage,
  });
  return data;
}

export default api;
