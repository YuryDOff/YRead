import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import MoodBoardPage from '../pages/MoodBoardPage';
import { defaultWrapper, wrapperWithSelectedImage, makeBookContextWrapper } from './test-wrappers';
import * as api from '../services/api';

vi.mock('../services/api', async () => {
  const actual = await vi.importActual('../services/api');
  return {
    ...(actual as object),
    getReferenceResults: vi.fn(() => Promise.resolve({ characters: {}, locations: {}, cover: { cover: [] } })),
    getCoverAnalysis: vi.fn(() => Promise.resolve(null)),
    updateCoverAnalysis: vi.fn(() => Promise.resolve({ id: 1, book_id: 1 })),
    analyzeCoverReference: vi.fn(() => Promise.resolve({ style_template: '', style_tags: [], mood_keywords: [] })),
    uploadReferenceImage: vi.fn(() => Promise.resolve({ url: '/static/up.jpg', thumbnail: '/static/up.jpg' })),
    getCharacters: vi.fn(() => Promise.resolve([])),
    getLocations: vi.fn(() => Promise.resolve([])),
    getArtefacts: vi.fn(() => Promise.resolve([])),
  };
});

function setupApiMock(overrides?: { analyzeCoverReference?: () => Promise<unknown> }) {
  if (overrides?.analyzeCoverReference) {
    vi.mocked(api.analyzeCoverReference).mockImplementation(overrides.analyzeCoverReference as () => Promise<api.I2TAnalysisResult>);
  }
  return api;
}

const mockI2TSuccess = vi.fn(() =>
  Promise.resolve({
    style_template: 'A style',
    style_tags: ['fantasy'],
    mood_keywords: ['dark'],
    lighting_description: 'Dramatic',
    color_palette_extracted: { dominant: ['#111'], accent: ['#222'] },
  } as api.I2TAnalysisResult),
);

const mockI2TFailure = vi.fn(() => Promise.reject(new Error('I2T failed')));

const mockFile = new File(['x'], 'cover.jpg', { type: 'image/jpeg' });

describe('MoodBoardPage', () => {
  beforeEach(() => {
    vi.mocked(api.getReferenceResults).mockResolvedValue({ characters: {}, locations: {}, cover: { cover: [] } });
    vi.mocked(api.getCoverAnalysis).mockResolvedValue(null);
    vi.mocked(api.updateCoverAnalysis).mockResolvedValue({ id: 1, book_id: 1 } as api.CoverAnalysisResponse);
    vi.mocked(api.analyzeCoverReference).mockImplementation(mockI2TSuccess);
  });

  it('simple mode renders only Style Reference tab', async () => {
    render(<MoodBoardPage />, { wrapper: makeBookContextWrapper({ analysisMode: 'simple' }) });
    expect(screen.getByText('Style Reference')).toBeInTheDocument();
    expect(screen.queryByText('Characters')).not.toBeInTheDocument();
  });

  it('pro mode renders all four tabs', async () => {
    render(<MoodBoardPage />, { wrapper: makeBookContextWrapper({ analysisMode: 'pro' }) });
    expect(screen.getByText('Style Reference')).toBeInTheDocument();
    expect(screen.getByText('Characters')).toBeInTheDocument();
    expect(screen.getByText('Locations')).toBeInTheDocument();
    expect(screen.getByText('Artefacts')).toBeInTheDocument();
  });

  it('Analyse style button not visible without selected image', async () => {
    render(<MoodBoardPage />, { wrapper: defaultWrapper() });
    await waitFor(() => {
      expect(screen.getByText('Upload cover reference')).toBeInTheDocument();
    });
    expect(screen.queryByRole('button', { name: /Analyse style/i })).not.toBeInTheDocument();
  });

  it('Analyse style button visible when image selected', async () => {
    vi.mocked(api.getReferenceResults).mockResolvedValue({
      characters: {},
      locations: {},
      cover: { cover: [{ url: '/static/ref.jpg', thumbnail: '/static/ref.jpg' }] },
    });
    render(<MoodBoardPage />, { wrapper: wrapperWithSelectedImage() });
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Analyse style/i })).toBeInTheDocument();
    });
  });

  it('clicking Analyse style calls analyze-cover-reference endpoint', async () => {
    vi.mocked(api.getReferenceResults).mockResolvedValue({
      characters: {},
      locations: {},
      cover: { cover: [{ url: '/static/ref.jpg', thumbnail: '/static/ref.jpg' }] },
    });
    const apiMock = setupApiMock();
    render(<MoodBoardPage />, { wrapper: wrapperWithSelectedImage() });
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Analyse style/i })).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole('button', { name: /Analyse style/i }));
    await waitFor(() => {
      expect(apiMock.analyzeCoverReference).toHaveBeenCalled();
    });
    expect(vi.mocked(api.analyzeCoverReference).mock.calls.length).toBeGreaterThanOrEqual(1);
  });

  it('success state shows StyleTemplateSummaryCard', async () => {
    setupApiMock({ analyzeCoverReference: mockI2TSuccess });
    vi.mocked(api.getReferenceResults).mockResolvedValue({
      characters: {},
      locations: {},
      cover: { cover: [{ url: '/static/ref.jpg', thumbnail: '/static/ref.jpg' }] },
    });
    render(<MoodBoardPage />, { wrapper: wrapperWithSelectedImage() });
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Analyse style/i })).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole('button', { name: /Analyse style/i }));
    expect(await screen.findByText(/View in Cover Brief/i)).toBeInTheDocument();
  });

  it('error state shows dismissible toast without blocking moodboard', async () => {
    setupApiMock({ analyzeCoverReference: mockI2TFailure });
    vi.mocked(api.getReferenceResults).mockResolvedValue({
      characters: {},
      locations: {},
      cover: { cover: [{ url: '/static/ref.jpg', thumbnail: '/static/ref.jpg' }] },
    });
    render(<MoodBoardPage />, { wrapper: wrapperWithSelectedImage() });
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Analyse style/i })).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole('button', { name: /Analyse style/i }));
    expect(await screen.findByText(/Style analysis failed/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Continue to Cover Brief/i })).toBeEnabled();
  });

  it('Analyse style does NOT auto-trigger on image upload', async () => {
    vi.mocked(api.analyzeCoverReference).mockClear();
    vi.mocked(api.getReferenceResults)
      .mockResolvedValueOnce({ characters: {}, locations: {}, cover: { cover: [] } })
      .mockResolvedValueOnce({ characters: {}, locations: {}, cover: { cover: [{ url: '/static/up.jpg' }] } });
    render(<MoodBoardPage />, { wrapper: defaultWrapper() });
    await waitFor(() => {
      expect(screen.getByTestId('cover-upload-input')).toBeInTheDocument();
    });
    const input = screen.getByTestId('cover-upload-input');
    fireEvent.change(input, { target: { files: [mockFile] } });
    await waitFor(() => {
      expect(api.uploadReferenceImage).toHaveBeenCalled();
    });
    expect(api.analyzeCoverReference).not.toHaveBeenCalled();
  });
});
