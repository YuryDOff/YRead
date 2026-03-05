import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronDown, ChevronRight, Loader2 } from 'lucide-react';
import { FeatureGate } from './FeatureGate';
import { generateCoverConcepts } from '../services/api';
import type { CoverAnalysisResponse } from '../services/api';
import type { Character, Location, Artefact } from '../services/api';

const COVER_TYPES = [
  { value: 'illustrated', label: 'Illustrated' },
  { value: 'photographic', label: 'Photographic' },
  { value: 'typographic', label: 'Typographic' },
  { value: 'abstract', label: 'Abstract' },
] as const;

const PANEL_A_STORAGE_KEY = 'noctua_panel_a_expanded';

interface CoverBriefEditorProps {
  bookId: number;
  analysisMode: 'simple' | 'pro';
  coverAnalysis: CoverAnalysisResponse | null;
  characters: Character[];
  locations: Location[];
  artefacts: Artefact[];
}

export default function CoverBriefEditor({
  bookId,
  analysisMode,
  coverAnalysis,
  characters,
  locations,
  artefacts,
}: CoverBriefEditorProps) {
  const navigate = useNavigate();
  const [coverType, setCoverType] = useState<string>('');
  const [primaryEntityKey, setPrimaryEntityKey] = useState<string>('');
  const [mergedPromptOverride, setMergedPromptOverride] = useState<string | null>(null);
  const [negativePromptOverride, setNegativePromptOverride] = useState<string | null>(null);
  const [panelAExpanded, setPanelAExpanded] = useState(() => {
    try {
      return localStorage.getItem(PANEL_A_STORAGE_KEY) === 'true';
    } catch {
      return false;
    }
  });
  const [generating, setGenerating] = useState(false);
  const [generateError, setGenerateError] = useState<string | null>(null);

  useEffect(() => {
    const stored = coverAnalysis?.cover_type ?? coverAnalysis?.cover_type;
    if (typeof stored === 'string') setCoverType(stored);
  }, [coverAnalysis]);

  useEffect(() => {
    try {
      localStorage.setItem(PANEL_A_STORAGE_KEY, String(panelAExpanded));
    } catch {
      /* ignore */
    }
  }, [panelAExpanded]);

  const assembledPrompt = coverAnalysis && (coverAnalysis as Record<string, unknown>).cover_t2i_prompt as string | undefined;
  const mergedPromptValue = mergedPromptOverride ?? assembledPrompt ?? '';
  const referenceStyleTemplate = coverAnalysis?.reference_style_template ?? undefined;
  const referenceImageUrl = coverAnalysis?.reference_image_url ?? undefined;

  const isSimple = analysisMode === 'simple';

  const primaryOptions = isSimple
    ? characters.map((c) => ({ key: `character-${c.id}`, type: 'character' as const, id: c.id, name: c.name }))
    : [
        ...characters.map((c) => ({ key: `character-${c.id}`, type: 'character' as const, id: c.id, name: c.name })),
        ...locations.map((l) => ({ key: `location-${l.id}`, type: 'location' as const, id: l.id, name: l.name })),
        ...artefacts.map((a) => ({ key: `artefact-${a.id}`, type: 'artefact' as const, id: a.id, name: a.name })),
      ];

  async function handleGenerate() {
    if (!bookId) return;
    setGenerating(true);
    setGenerateError(null);
    try {
      const conceptCount = isSimple ? 3 : 6;
      const primaryLabel = primaryOptions.find((o) => o.key === primaryEntityKey)?.name ?? '';
      const instruction = [
        coverType ? `Cover type: ${coverType}` : '',
        primaryLabel ? `Primary element: ${primaryLabel}` : '',
      ].filter(Boolean).join('. ');

      await generateCoverConcepts(bookId, {
        concept_count: conceptCount,
        user_instruction: instruction || undefined,
      });
      navigate(`/books/${bookId}/studio/cover`);
    } catch (err) {
      console.error('Cover generation failed', err);
      setGenerateError('Cover generation failed. Please try again.');
    } finally {
      setGenerating(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="p-4 rounded-xl border border-sepia/15 bg-white/50 space-y-4">
        <div>
          <label className="block font-ui text-sm font-medium text-charcoal mb-1">Cover type</label>
          <select
            data-testid="cover-type-selector"
            value={coverType}
            onChange={(e) => setCoverType(e.target.value)}
            className="w-full max-w-xs px-3 py-2 rounded-lg border border-sepia/20 font-ui text-sm"
          >
            <option value="">—</option>
            {COVER_TYPES.map((t) => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block font-ui text-sm font-medium text-charcoal mb-1">Primary element</label>
          <select
            value={primaryEntityKey}
            onChange={(e) => setPrimaryEntityKey(e.target.value)}
            className="w-full max-w-xs px-3 py-2 rounded-lg border border-sepia/20 font-ui text-sm"
          >
            <option value="">—</option>
            {primaryOptions.map((opt) => (
              <option key={opt.key} value={opt.key}>{opt.name}</option>
            ))}
          </select>
        </div>

        {referenceImageUrl && (
          <div>
            <span className="block font-ui text-xs text-sepia mb-1">Style reference</span>
            <img
              src={referenceImageUrl}
              alt="Cover style reference"
              className="w-24 h-24 object-cover rounded-lg border border-sepia/20"
            />
          </div>
        )}

        {!isSimple && (
          <>
            <div data-testid="prompt-panel-b">
              <label className="block font-ui text-sm font-medium text-charcoal mb-1">Merged Prompt</label>
              <textarea
                value={mergedPromptValue}
                onChange={(e) => setMergedPromptOverride(e.target.value)}
                rows={4}
                className="w-full px-3 py-2 rounded-lg border border-sepia/20 font-ui text-sm"
                aria-label="Merged Prompt"
              />
            </div>

            <div>
              <button
                type="button"
                onClick={() => setPanelAExpanded((p) => !p)}
                className="flex items-center gap-1 font-ui text-sm text-sepia hover:text-charcoal"
              >
                {panelAExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                Advanced
              </button>
              {panelAExpanded && referenceStyleTemplate && (
                <div className="mt-2 p-3 rounded-lg bg-sepia/5 border border-sepia/15">
                  <span className="block font-ui text-xs text-sepia mb-1">Style Template</span>
                  <p className="font-body text-sm text-charcoal whitespace-pre-wrap">{referenceStyleTemplate}</p>
                </div>
              )}
            </div>

            <FeatureGate plan="pro">
              <div>
                <label className="block font-ui text-sm font-medium text-charcoal mb-1">Negative prompt</label>
                <textarea
                  value={negativePromptOverride ?? ''}
                  onChange={(e) => setNegativePromptOverride(e.target.value || null)}
                  rows={2}
                  className="w-full px-3 py-2 rounded-lg border border-sepia/20 font-ui text-sm"
                  aria-label="Negative prompt"
                />
              </div>
            </FeatureGate>
          </>
        )}

        <button
          type="button"
          onClick={handleGenerate}
          disabled={generating}
          className="px-6 py-2.5 rounded-lg font-ui font-semibold text-paper-cream
                     bg-midnight hover:bg-midnight/90 transition-colors
                     disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {generating ? (
            <span className="flex items-center gap-2">
              <Loader2 size={16} className="animate-spin" />
              Generating…
            </span>
          ) : (
            'Generate Cover'
          )}
        </button>
        {generateError && (
          <p className="font-ui text-xs text-red-600 mt-2">{generateError}</p>
        )}
      </div>
    </div>
  );
}
