/**
 * API client for the Reading Reinvented backend.
 */
import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
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
}

export interface Location {
  id: number;
  book_id: number;
  name: string;
  visual_description: string | null;
  atmosphere: string | null;
  reference_image_url: string | null;
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

export interface ReferenceImages {
  characters: Record<string, { url: string; width: number; height: number; thumbnail: string }[]>;
  locations: Record<string, { url: string; width: number; height: number; thumbnail: string }[]>;
}

/* ------------------------------------------------------------------ */
/* Book endpoints                                                      */
/* ------------------------------------------------------------------ */

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

export async function chunkBook(bookId: number): Promise<{ status: string; message: string }> {
  const { data } = await api.post(`/books/${bookId}/chunk`);
  return data;
}

export async function analyzeBook(
  bookId: number,
  params: {
    style_category: string;
    illustration_frequency: number;
    layout_style: string;
    is_well_known: boolean;
    author?: string;
  },
): Promise<{ status: string; estimated_time: number }> {
  const { data } = await api.post(`/books/${bookId}/analyze`, params);
  return data;
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

export async function searchReferences(bookId: number): Promise<ReferenceImages> {
  const { data } = await api.post<ReferenceImages>(`/books/${bookId}/search-references`);
  return data;
}

export async function approveVisualBible(
  bookId: number,
  selections: {
    character_selections: Record<number, string>;
    location_selections: Record<number, string>;
  },
) {
  const { data } = await api.post(`/books/${bookId}/visual-bible/approve`, selections);
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
