import { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Loader2, X, ImagePlus, ExternalLink } from 'lucide-react';
import { useBook } from '../context/BookContext';
import {
  getReferenceResults,
  getCoverAnalysis,
  updateCoverAnalysis,
  uploadReferenceImage,
  analyzeCoverReference,
  getCoverImages,
  getCharacters,
  getLocations,
  getArtefacts,
  type ReferenceImageItem,
  type I2TAnalysisResult,
  type CoverAnalysisResponse,
  type Character,
  type Location,
  type Artefact,
} from '../services/api';

type TabId = 'style' | 'characters' | 'locations' | 'artefacts';

function StyleTemplateSummaryCard({
  result,
  onDismiss,
  onViewCoverBrief,
}: {
  result: I2TAnalysisResult;
  onDismiss: () => void;
  onViewCoverBrief: () => void;
}) {
  const styleTags = Array.isArray(result.style_tags) ? result.style_tags : [];
  const moodKeywords = Array.isArray(result.mood_keywords) ? result.mood_keywords : [];
  const palette = result.color_palette_extracted as { dominant?: string[]; accent?: string[] } | undefined;
  const dominant = Array.isArray(palette?.dominant) ? palette.dominant : [];
  const accent = Array.isArray(palette?.accent) ? palette.accent : [];

  return (
    <div className="rounded-lg border border-sepia/30 bg-white p-4 shadow-sm relative">
      <button
        type="button"
        onClick={onDismiss}
        className="absolute top-2 right-2 text-charcoal hover:text-ink-black"
        aria-label="Dismiss"
      >
        <X className="w-5 h-5" />
      </button>
      <h3 className="font-display text-lg text-ink-black mb-2">Style summary</h3>
      {styleTags.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-2">
          {styleTags.map((tag, i) => (
            <span key={i} className="px-2 py-0.5 rounded bg-dusty-rose/20 text-sepia text-sm">
              {tag}
            </span>
          ))}
        </div>
      )}
      {moodKeywords.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-2">
          {moodKeywords.map((kw, i) => (
            <span key={i} className="px-2 py-0.5 rounded bg-sage/25 text-charcoal text-sm">
              {kw}
            </span>
          ))}
        </div>
      )}
      {(dominant.length > 0 || accent.length > 0) && (
        <div className="flex items-center gap-3 mb-2">
          {dominant.length > 0 && (
            <div className="flex items-center gap-1">
              <span className="text-sm text-sepia">Dominant:</span>
              {dominant.slice(0, 5).map((c, i) => (
                <span
                  key={i}
                  className="w-5 h-5 rounded border border-sepia/30"
                  style={{ backgroundColor: String(c).startsWith('#') ? c : `#${c}` }}
                  title={String(c)}
                />
              ))}
            </div>
          )}
          {accent.length > 0 && (
            <div className="flex items-center gap-1">
              <span className="text-sm text-sepia">Accent:</span>
              {accent.slice(0, 3).map((c, i) => (
                <span
                  key={i}
                  className="w-4 h-4 rounded border border-sepia/30"
                  style={{ backgroundColor: String(c).startsWith('#') ? c : `#${c}` }}
                  title={String(c)}
                />
              ))}
            </div>
          )}
        </div>
      )}
      {result.lighting_description && (
        <p className="text-sm text-charcoal mb-2">{result.lighting_description}</p>
      )}
      <button
        type="button"
        onClick={onViewCoverBrief}
        className="text-sm text-midnight underline hover:no-underline"
      >
        View in Cover Brief editor
      </button>
    </div>
  );
}

export default function MoodBoardPage() {
  const { bookId } = useParams<{ bookId: string }>();
  const navigate = useNavigate();
  const ctx = useBook();
  const id = bookId ? Number(bookId) : null;

  const [coverImages, setCoverImages] = useState<ReferenceImageItem[]>([]);
  const [coverAnalysisId, setCoverAnalysisId] = useState<number | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [i2tResult, setI2tResult] = useState<I2TAnalysisResult | null>(null);
  const [errorToast, setErrorToast] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [characters, setCharacters] = useState<Character[]>([]);
  const [locations, setLocations] = useState<Location[]>([]);
  const [artefacts, setArtefacts] = useState<Artefact[]>([]);
  const [refsLoaded, setRefsLoaded] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const analysisMode = (ctx.book && (ctx.book as { analysis_mode?: string }).analysis_mode === 'simple') ? 'simple' : 'pro';
  const hasSelectedCoverImage = coverImages.length >= 1;
  const firstCoverImageUrl = coverImages[0]?.url;

  useEffect(() => {
    if (!id || !ctx.book) return;
    if (ctx.book.id !== id) {
      ctx.setBook(null);
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const [refs, coverAnalysis] = await Promise.all([
          getReferenceResults(id),
          getCoverAnalysis(id).catch(() => null),
        ]);
        if (cancelled) return;
        const cover = getCoverImages(refs);
        const selectedCovers = cover.filter(
          (img) => img.is_selected_for_reference === 1 || img.source === 'upload'
        );
        setCoverImages(selectedCovers.length > 0 ? selectedCovers : cover);
        ctx.setReferenceImages(refs);
        let analysisId = coverAnalysis && (coverAnalysis as CoverAnalysisResponse).id;
        if (!analysisId) {
          const created = await updateCoverAnalysis(id, {}).catch(() => null);
          if (cancelled) return;
          if (created && (created as CoverAnalysisResponse).id) analysisId = (created as CoverAnalysisResponse).id;
        }
        if (analysisId) setCoverAnalysisId(analysisId);
      } catch {
        if (!cancelled) setCoverImages([]);
      } finally {
        if (!cancelled) setRefsLoaded(true);
      }
    })();
    return () => { cancelled = true; };
  }, [id, ctx.book?.id]);

  useEffect(() => {
    if (!id || analysisMode !== 'pro') return;
    (async () => {
      try {
        const [chars, locs, arts] = await Promise.all([
          getCharacters(id),
          getLocations(id),
          getArtefacts(id),
        ]);
        setCharacters(chars);
        setLocations(locs);
        setArtefacts(arts);
      } catch {
        /* ignore */
      }
    })();
  }, [id, analysisMode]);

  async function handleUploadCoverRef(file: File) {
    if (!id || coverAnalysisId == null) return;
    setUploading(true);
    try {
      const uploaded = await uploadReferenceImage(id, 'cover', coverAnalysisId, file);
      const refs = await getReferenceResults(id);
      const cover = getCoverImages(refs);
      const filtered = cover.filter(
        (img) => img.is_selected_for_reference === 1 || img.source === 'upload'
      );
      if (filtered.length === 0 && uploaded?.url) {
        setCoverImages([uploaded, ...cover.slice(0, 2)]);
      } else {
        setCoverImages(filtered.length > 0 ? filtered : cover);
      }
      ctx.setReferenceImages(refs);
    } catch {
      setErrorToast('Upload failed. Please try again.');
    } finally {
      setUploading(false);
    }
  }

  async function handleAnalyseStyle() {
    if (!id || !firstCoverImageUrl) return;
    setAnalyzing(true);
    setErrorToast(null);
    try {
      const base = typeof window !== 'undefined' && window.location.origin ? window.location.origin : '';
      const imageUrl = firstCoverImageUrl.startsWith('http') ? firstCoverImageUrl : `${base}${firstCoverImageUrl}`;
      const result = await analyzeCoverReference(id, { image_url: imageUrl, mode: 'cover' });
      setI2tResult(result);
    } catch {
      setErrorToast('Style analysis failed. You can still continue.');
    } finally {
      setAnalyzing(false);
    }
  }

  const tabs: { id: TabId; label: string }[] =
    analysisMode === 'simple'
      ? [{ id: 'style', label: 'Style Reference' }]
      : [
          { id: 'style', label: 'Style Reference' },
          { id: 'characters', label: 'Characters' },
          { id: 'locations', label: 'Locations' },
          { id: 'artefacts', label: 'Artefacts' },
        ];

  const [activeTab, setActiveTab] = useState<TabId>('style');

  if (!id || (ctx.book && ctx.book.id !== id)) {
    return (
      <div className="min-h-screen bg-paper-cream flex items-center justify-center px-4">
        <p className="font-ui text-sepia">Loading...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-paper-cream p-6 max-w-5xl mx-auto">
      <h1 className="font-display text-2xl text-ink-black mb-6">Mood Board</h1>

      <div className="flex gap-2 border-b border-sepia/30 mb-6">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            type="button"
            role="tab"
            aria-label={tab.label}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 font-ui text-sm ${activeTab === tab.id ? 'border-b-2 border-midnight text-ink-black' : 'text-sepia hover:text-charcoal'}`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {errorToast && (
        <div className="mb-4 flex items-center justify-between rounded bg-dusty-rose/20 px-4 py-2 text-charcoal">
          <span>{errorToast}</span>
          <button type="button" onClick={() => setErrorToast(null)} aria-label="Dismiss">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {activeTab === 'style' && (
        <div className="space-y-4">
          <div className="flex flex-wrap items-center gap-2">
            <input
              ref={fileInputRef}
              type="file"
              accept=".jpg,.jpeg,.png,.webp"
              className="hidden"
              data-testid="cover-upload-input"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) handleUploadCoverRef(f);
                e.target.value = '';
              }}
            />
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading || coverAnalysisId == null}
              className="inline-flex items-center gap-2 px-3 py-2 rounded bg-midnight text-white font-ui text-sm disabled:opacity-50"
            >
              {uploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <ImagePlus className="w-4 h-4" />}
              Upload cover reference
            </button>
            <a
              href={`/books/${id}/review-search`}
              className="inline-flex items-center gap-1 text-midnight underline text-sm"
              onClick={(e) => {
                e.preventDefault();
                navigate(`/books/${id}/review-search`);
              }}
            >
              Search for similar covers
              <ExternalLink className="w-3 h-3" />
            </a>
            {hasSelectedCoverImage && (
              <button
                type="button"
                onClick={handleAnalyseStyle}
                disabled={analyzing}
                className="inline-flex items-center gap-2 px-3 py-2 rounded bg-golden text-ink-black font-ui text-sm disabled:opacity-70"
              >
                {analyzing ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Extracting style...
                  </>
                ) : (
                  'Analyse style'
                )}
              </button>
            )}
          </div>

          {i2tResult && (
            <StyleTemplateSummaryCard
              result={i2tResult}
              onDismiss={() => setI2tResult(null)}
              onViewCoverBrief={() => navigate(`/books/${id}/cover-brief`)}
            />
          )}

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
            {coverImages.map((img, i) => (
              <div key={i} className="rounded border border-sepia/30 overflow-hidden bg-white aspect-[2/3]">
                <img
                  src={img.thumbnail || img.url}
                  alt={`Cover reference ${i + 1}`}
                  className="w-full h-full object-cover"
                />
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'characters' && (
        <div className="space-y-4">
          {characters.map((c) => (
            <div key={c.id} className="rounded border border-sepia/30 p-3 bg-white">
              <h3 className="font-display text-ink-black">{c.name}</h3>
              <p className="text-sm text-sepia">Image grid by entity — upload & approve to Visual Bible</p>
            </div>
          ))}
        </div>
      )}
      {activeTab === 'locations' && (
        <div className="space-y-4">
          {locations.map((l) => (
            <div key={l.id} className="rounded border border-sepia/30 p-3 bg-white">
              <h3 className="font-display text-ink-black">{l.name}</h3>
              <p className="text-sm text-sepia">Image grid by entity — upload & approve to Visual Bible</p>
            </div>
          ))}
        </div>
      )}
      {activeTab === 'artefacts' && (
        <div className="space-y-4">
          {artefacts.map((a) => (
            <div key={a.id} className="rounded border border-sepia/30 p-3 bg-white">
              <h3 className="font-display text-ink-black">{a.name}</h3>
              <p className="text-sm text-sepia">Image grid by entity — upload & approve to Visual Bible</p>
            </div>
          ))}
        </div>
      )}

      <div className="mt-10 pt-6 border-t border-sepia/30 flex justify-end">
        <button
          type="button"
          onClick={() => navigate(`/books/${id}/cover-brief`)}
          className="px-4 py-2 rounded bg-midnight text-white font-ui"
        >
          Continue to Cover Brief
        </button>
      </div>
    </div>
  );
}
