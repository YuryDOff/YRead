import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import { useBook } from '../context/BookContext';
import { useAuth } from '../context/AuthContext';
import {
  getCoverConcepts,
  generateCoverConcepts,
  selectCoverConcept,
  type CoverConceptResponse,
} from '../services/api';

const POLL_INTERVAL_MS = 3000;
const KDP_NOTE =
  'Final cover will be exported at 2560×1600px, 300dpi, with 0.125" bleed — KDP compatible';

export default function CoverStudioPage() {
  const { bookId } = useParams<{ bookId: string }>();
  const navigate = useNavigate();
  const ctx = useBook();
  const auth = useAuth();
  const id = bookId ? Number(bookId) : null;

  const [concepts, setConcepts] = useState<CoverConceptResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [selectedConceptId, setSelectedConceptId] = useState<number | null>(null);
  const [regenerating, setRegenerating] = useState(false);

  const plan = auth.user?.plan ?? 'simple';
  const maxConcepts = plan === 'simple' ? 3 : 6;
  const isPro = plan === 'pro';

  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    (async () => {
      try {
        const list = await getCoverConcepts(id);
        if (!cancelled) {
          setConcepts(list);
          const sel = list.find((c) => c.is_selected === 1);
          if (sel) setSelectedConceptId(sel.id);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [id]);

  useEffect(() => {
    if (!id || !concepts.length) return;
    const anyGenerating = concepts.some((c) => c.status === 'generating');
    setGenerating(anyGenerating);
    if (!anyGenerating) return;
    const t = setInterval(async () => {
      try {
        const list = await getCoverConcepts(id);
        setConcepts(list);
        const sel = list.find((c) => c.is_selected === 1);
        if (sel) setSelectedConceptId(sel.id);
        const still = list.some((c) => c.status === 'generating');
        if (!still) setGenerating(false);
      } catch {
        /* ignore */
      }
    }, POLL_INTERVAL_MS);
    return () => clearInterval(t);
  }, [id, concepts.map((c) => c.status).join(',')]);

  async function handleRegenerate() {
    if (!id) return;
    setRegenerating(true);
    try {
      const userInstruction =
        (typeof localStorage !== 'undefined' && localStorage.getItem('noctua_cover_user_instruction')) || undefined;
      const { concepts: next } = await generateCoverConcepts(id, {
        concept_count: maxConcepts,
        user_instruction: userInstruction ?? undefined,
      });
      setConcepts(next);
      setSelectedConceptId(null);
      setGenerating(true);
    } finally {
      setRegenerating(false);
    }
  }

  async function handleSelect(conceptId: number) {
    if (!id) return;
    await selectCoverConcept(id, conceptId);
    setSelectedConceptId(conceptId);
    const list = await getCoverConcepts(id);
    setConcepts(list);
  }

  function handleContinue() {
    if (selectedConceptId != null && id) {
      if (typeof localStorage !== 'undefined') {
        const c = concepts.find((x) => x.id === selectedConceptId);
        if (c?.image_path) localStorage.setItem('noctua_selected_cover_url', c.image_path);
      }
      navigate(`/books/${id}/studio/text`);
    }
  }

  if (!id || (ctx.book && ctx.book.id !== id)) {
    return (
      <div className="min-h-screen bg-paper-cream flex items-center justify-center px-4">
        <p className="font-ui text-sepia">Loading...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-paper-cream p-6 max-w-5xl mx-auto">
      <h1 className="font-display text-2xl text-ink-black mb-4">Cover Studio</h1>
      <p className="text-sm text-sepia mb-4">{KDP_NOTE}</p>

      {generating && (
        <div className="flex items-center gap-2 mb-4 text-charcoal">
          <Loader2 className="w-5 h-5 animate-spin" />
          <span>Generating concepts...</span>
        </div>
      )}

      <div className="mb-4 flex gap-2">
        <button
          type="button"
          onClick={handleRegenerate}
          disabled={regenerating}
          className="px-4 py-2 rounded bg-midnight text-white font-ui text-sm disabled:opacity-50"
        >
          {regenerating ? 'Starting...' : 'Regenerate'}
        </button>
      </div>

      {loading ? (
        <p className="font-ui text-sepia">Loading concepts...</p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4" data-testid="concept-grid">
          {concepts.slice(0, maxConcepts).map((c) => (
            <div
              key={c.id}
              data-testid="concept-card"
              className="rounded border border-sepia/30 bg-white overflow-hidden"
            >
              <div className="aspect-[2/3] bg-charcoal/10 flex items-center justify-center">
                {c.status === 'complete' && c.image_path ? (
                  <img
                    src={c.image_path.startsWith('http') ? c.image_path : `${import.meta.env.VITE_API_URL || ''}${c.image_path}`}
                    alt={`Concept ${c.concept_index}`}
                    className="w-full h-full object-cover"
                  />
                ) : c.status === 'generating' ? (
                  <Loader2 className="w-10 h-10 animate-spin text-sepia" />
                ) : c.status === 'failed' ? (
                  <span className="text-sm text-dusty-rose">Failed</span>
                ) : (
                  <span className="text-sm text-sepia">Pending</span>
                )}
              </div>
              <div className="p-2 flex flex-col gap-1">
                <button
                  type="button"
                  onClick={() => c.status === 'complete' && handleSelect(c.id)}
                  disabled={c.status !== 'complete'}
                  className="px-2 py-1 rounded border border-sepia/30 text-sm font-ui disabled:opacity-50"
                >
                  Select
                </button>
                {isPro && c.prompt_used && (
                  <details className="text-xs text-sepia">
                    <summary>Params</summary>
                    <pre className="whitespace-pre-wrap mt-1 overflow-auto max-h-24">{c.prompt_used}</pre>
                  </details>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="mt-8 pt-6 border-t border-sepia/30 flex justify-end">
        <button
          type="button"
          onClick={handleContinue}
          disabled={selectedConceptId == null}
          className="px-4 py-2 rounded bg-midnight text-white font-ui disabled:opacity-50"
        >
          Continue to Typography
        </button>
      </div>
    </div>
  );
}
