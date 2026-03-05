import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import { useBook } from '../context/BookContext';
import {
  getCharacters,
  getLocations,
  getArtefacts,
  getCoverAnalysis,
  type Character,
  type Location,
  type Artefact,
  type CoverAnalysisResponse,
} from '../services/api';
import CoverBriefEditor from '../components/CoverBriefEditor';

export default function CoverBriefPage() {
  const navigate = useNavigate();
  const ctx = useBook();
  const [characters, setCharacters] = useState<Character[]>([]);
  const [locations, setLocations] = useState<Location[]>([]);
  const [artefacts, setArtefacts] = useState<Artefact[]>([]);
  const [coverAnalysis, setCoverAnalysis] = useState<CoverAnalysisResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const analysisMode =
    (ctx.book && (ctx.book as { analysis_mode?: string }).analysis_mode === 'simple')
      ? 'simple'
      : 'pro';

  useEffect(() => {
    if (!ctx.book) { navigate('/'); return; }
    (async () => {
      try {
        const [chars, locs, arts, cover] = await Promise.all([
          getCharacters(ctx.book!.id),
          getLocations(ctx.book!.id).catch(() => []),
          getArtefacts(ctx.book!.id).catch(() => []),
          getCoverAnalysis(ctx.book!.id).catch(() => null),
        ]);
        setCharacters(chars);
        setLocations(locs);
        setArtefacts(arts);
        setCoverAnalysis(cover);
      } finally {
        setLoading(false);
      }
    })();
  }, [ctx.book, navigate]);

  if (loading) {
    return (
      <div className="min-h-screen bg-paper-cream flex items-center justify-center">
        <Loader2 size={32} className="animate-spin text-golden" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-paper-cream px-4 py-10">
      <div className="max-w-2xl mx-auto space-y-6">
        <div className="text-center space-y-1">
          <h1 className="font-display text-3xl font-semibold text-charcoal">Cover Brief</h1>
          <p className="font-body text-sm text-sepia">{ctx.book?.title}</p>
          <p className="font-ui text-xs text-sepia/70 max-w-md mx-auto">
            Select your cover type and primary character. Then generate your cover concepts.
          </p>
        </div>
        {ctx.book && (
          <CoverBriefEditor
            bookId={ctx.book.id}
            analysisMode={analysisMode}
            coverAnalysis={coverAnalysis}
            characters={characters}
            locations={locations}
            artefacts={artefacts}
          />
        )}
      </div>
    </div>
  );
}
