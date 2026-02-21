import { useEffect, useState, useRef } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Search, Loader2, ArrowLeft, User, MapPin, Film } from 'lucide-react';
import { useBook } from '../context/BookContext';
import {
  getProposedSearchQueries,
  patchEntitySummaries,
  searchReferences,
  updateScene,
  ENABLED_PROVIDERS_STORAGE_KEY,
  type ProposedEntity,
  type ProposedScene,
} from '../services/api';
import { getPreferredSearchProvider } from '../hooks/useSettings';

export default function ReviewSearchPage() {
  const navigate = useNavigate();
  const { bookId: bookIdParam } = useParams<{ bookId?: string }>();
  const ctx = useBook();
  const bookId = ctx.book?.id ?? (bookIdParam ? Number(bookIdParam) : undefined);

  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [characters, setCharacters] = useState<(ProposedEntity & { queries: string[] })[]>([]);
  const [locations, setLocations] = useState<(ProposedEntity & { queries: string[] })[]>([]);
  const [scenes, setScenes] = useState<ProposedScene[]>([]);
  const [searchProvider, setSearchProvider] = useState<'unsplash' | 'serpapi' | ''>('');
  const [searchEntityTypes, setSearchEntityTypes] = useState<'characters' | 'locations' | 'both'>('both');
  const sceneDraftTimers = useRef<Record<number, ReturnType<typeof setTimeout>>>({});

  const storageKey = bookId ? `review_search_options_${bookId}` : null;

  useEffect(() => {
    if (storageKey) {
      try {
        const raw = localStorage.getItem(storageKey);
        if (raw) {
          const parsed = JSON.parse(raw) as { searchProvider?: string; searchEntityTypes?: string };
          if (parsed.searchProvider !== undefined) setSearchProvider(parsed.searchProvider as 'unsplash' | 'serpapi' | '');
          if (parsed.searchEntityTypes !== undefined) setSearchEntityTypes(parsed.searchEntityTypes as 'characters' | 'locations' | 'both');
        }
      } catch {
        // ignore
      }
    }
  }, [storageKey]);

  useEffect(() => {
    if (!bookId) {
      navigate(bookIdParam ? `/books/${bookIdParam}/analysis-review` : '/');
      return;
    }
    (async () => {
      try {
        const data = await getProposedSearchQueries(bookId, true);
        setCharacters(
          data.characters.map((c) => ({
            ...c,
            queries: c.proposed_queries?.length ? [...c.proposed_queries] : [''],
            text_to_image_prompt: c.text_to_image_prompt ?? '',
          })),
        );
        setLocations(
          data.locations.map((l) => ({
            ...l,
            queries: l.proposed_queries?.length ? [...l.proposed_queries] : [''],
            text_to_image_prompt: l.text_to_image_prompt ?? '',
          })),
        );
        setScenes(data.scenes ?? []);
      } catch {
        navigate(bookIdParam ? `/books/${bookIdParam}/analysis-review` : '/');
      } finally {
        setLoading(false);
      }
    })();
  }, [bookId, bookIdParam, navigate]);

  // When only one entity type exists, default "Search for" to that type and persist
  useEffect(() => {
    if (loading) return;
    const hasCharacters = characters.length > 0;
    const hasLocations = locations.length > 0;
    const allowed: Array<'characters' | 'locations' | 'both'> = hasCharacters && hasLocations
      ? ['both', 'characters', 'locations']
      : hasCharacters
        ? ['characters']
        : hasLocations
          ? ['locations']
          : [];
    const valid = allowed.includes(searchEntityTypes);
    if (allowed.length === 1) {
      const only = allowed[0];
      setSearchEntityTypes(only);
      if (storageKey) {
        try {
          localStorage.setItem(storageKey, JSON.stringify({ searchProvider, searchEntityTypes: only }));
        } catch {
          // ignore
        }
      }
    } else if (allowed.length > 1 && !valid) {
      setSearchEntityTypes(allowed[0]);
    }
  }, [loading, characters.length, locations.length, storageKey, searchProvider]); // searchEntityTypes intentionally not in deps to avoid overwriting user choice when both exist

  function setCharSummary(id: number, summary: string) {
    setCharacters((prev) =>
      prev.map((c) => (c.id === id ? { ...c, summary } : c)),
    );
  }
  function setCharQueries(id: number, queries: string[]) {
    setCharacters((prev) =>
      prev.map((c) => (c.id === id ? { ...c, queries } : c)),
    );
  }
  function setCharPrompt(id: number, text_to_image_prompt: string) {
    setCharacters((prev) =>
      prev.map((c) => (c.id === id ? { ...c, text_to_image_prompt } : c)),
    );
  }
  function setLocSummary(id: number, summary: string) {
    setLocations((prev) =>
      prev.map((l) => (l.id === id ? { ...l, summary } : l)),
    );
  }
  function setLocQueries(id: number, queries: string[]) {
    setLocations((prev) =>
      prev.map((l) => (l.id === id ? { ...l, queries } : l)),
    );
  }
  function setLocPrompt(id: number, text_to_image_prompt: string) {
    setLocations((prev) =>
      prev.map((l) => (l.id === id ? { ...l, text_to_image_prompt } : l)),
    );
  }

  async function handleRunSearch() {
    if (!bookId) return;
    const hasChars = characters.length > 0;
    const hasLocs = locations.length > 0;
    const effectiveType: 'characters' | 'locations' | 'both' =
      hasChars && hasLocs ? searchEntityTypes : hasChars ? 'characters' : 'locations';

    setRunning(true);
    try {
      await patchEntitySummaries(bookId, {
        characters: characters.map((c) => ({
          id: c.id,
          physical_description: c.summary || undefined,
          text_to_image_prompt: c.text_to_image_prompt ?? '',
        })),
        locations: locations.map((l) => ({
          id: l.id,
          visual_description: l.summary || undefined,
          text_to_image_prompt: l.text_to_image_prompt ?? '',
        })),
      });

      // Always send queries for every entity on the page so backend uses only these (no fallback to auto-built).
      const charQueries: Record<string, string[]> = {};
      characters.forEach((c) => {
        charQueries[String(c.id)] = c.queries.map((s) => s.trim()).filter(Boolean);
      });
      const locQueries: Record<string, string[]> = {};
      locations.forEach((l) => {
        locQueries[String(l.id)] = l.queries.map((s) => s.trim()).filter(Boolean);
      });

      const preferredProvider = searchProvider || getPreferredSearchProvider();
      let enabledProviders: string[] | undefined;
      try {
        const raw = localStorage.getItem(ENABLED_PROVIDERS_STORAGE_KEY);
        if (raw) {
          const parsed = JSON.parse(raw);
          if (Array.isArray(parsed) && parsed.length > 0) enabledProviders = parsed;
        }
      } catch {
        // ignore
      }
      const refs = await searchReferences(bookId, true, {
        character_queries: charQueries,
        location_queries: locQueries,
        ...(preferredProvider ? { preferred_provider: preferredProvider } : {}),
        search_entity_types: effectiveType,
        ...(enabledProviders ? { enabled_providers: enabledProviders } : {}),
      });
      // Keep previous reference images for the entity type we did not search
      const prev = ctx.referenceImages;
      ctx.setReferenceImages({
        characters: effectiveType === 'locations' && prev?.characters ? prev.characters : refs.characters,
        locations: effectiveType === 'characters' && prev?.locations ? prev.locations : refs.locations,
      });
      if (storageKey) {
        try {
          localStorage.setItem(storageKey, JSON.stringify({ searchProvider, searchEntityTypes: effectiveType }));
        } catch {
          // ignore
        }
      }
      const initialTab = effectiveType === 'locations' ? 'locations' : 'characters';
      navigate(bookId ? `/books/${bookId}/review-search-result` : '/review-search-result', { state: { initialTab } });
    } catch (err) {
      console.error('Search failed', err);
      alert('Reference image search failed. Please try again.');
    } finally {
      setRunning(false);
    }
  }

  function handleSceneDraftChange(sceneId: number, draft: string) {
    setScenes((prev) =>
      prev.map((s) => (s.id === sceneId ? { ...s, scene_prompt_draft: draft } : s)),
    );
    if (!bookId) return;
    clearTimeout(sceneDraftTimers.current[sceneId]);
    sceneDraftTimers.current[sceneId] = setTimeout(() => {
      updateScene(bookId, sceneId, { scene_prompt_draft: draft }).catch(console.error);
    }, 800);
  }

  if (!bookId) return null;
  if (loading) {
    return (
      <div className="min-h-screen bg-paper-cream flex items-center justify-center">
        <Loader2 size={32} className="animate-spin text-golden" />
      </div>
    );
  }

  const hasCharacters = characters.length > 0;
  const hasLocations = locations.length > 0;
  const searchForOptions: Array<{ value: 'characters' | 'locations' | 'both'; label: string }> =
    hasCharacters && hasLocations
      ? [
          { value: 'both', label: 'Characters & locations' },
          { value: 'characters', label: 'Characters only' },
          { value: 'locations', label: 'Locations only' },
        ]
      : hasCharacters
        ? [{ value: 'characters', label: 'Characters only' }]
        : hasLocations
          ? [{ value: 'locations', label: 'Locations only' }]
          : [];

  const effectiveSearchEntityTypes = searchForOptions.some((o) => o.value === searchEntityTypes)
    ? searchEntityTypes
    : (searchForOptions[0]?.value ?? 'both');
  const totalEntities = characters.length + locations.length;
  const searchableCount =
    effectiveSearchEntityTypes === 'both' ? totalEntities
    : effectiveSearchEntityTypes === 'characters' ? characters.length
    : locations.length;
  const canRunSearch = searchableCount > 0;

  return (
    <div className="min-h-screen bg-paper-cream px-4 py-12">
      <div className="max-w-3xl mx-auto space-y-8">
        <div className="text-center space-y-2">
          <h1 className="font-display text-3xl font-semibold text-charcoal">
            Review summaries & search queries
          </h1>
          <p className="text-sepia font-body text-sm">
            {ctx.book?.title}
          </p>
          <p className="text-sepia/70 font-ui text-xs max-w-lg mx-auto">
            Edit the AI summary, reference image search queries, and text-to-image prompt per entity.
            Then run the search.
          </p>
        </div>

        {/* Search options */}
        <section className="p-4 rounded-xl border border-sepia/15 bg-white/50 space-y-4">
          <h2 className="font-display text-sm font-semibold text-charcoal uppercase tracking-wide">
            Search options
          </h2>
          <div className="flex flex-wrap gap-6">
            <div className="space-y-2">
              <label className="block font-ui text-xs text-sepia">Search engine</label>
              <select
                value={searchProvider}
                onChange={(e) => {
                  const v = (e.target.value || '') as 'unsplash' | 'serpapi' | '';
                  setSearchProvider(v);
                  if (storageKey) try { localStorage.setItem(storageKey, JSON.stringify({ searchProvider: v, searchEntityTypes })); } catch { /* ignore */ }
                }}
                className="px-3 py-2 rounded-lg border border-sepia/20 font-ui text-sm text-charcoal
                           bg-white focus:border-golden focus:outline-none cursor-pointer"
              >
                <option value="">Default (from Settings)</option>
                <option value="unsplash">Unsplash</option>
                <option value="serpapi">SerpAPI</option>
              </select>
            </div>
            <div className="space-y-2">
              <label className="block font-ui text-xs text-sepia">Search for</label>
              <select
                value={effectiveSearchEntityTypes}
                onChange={(e) => {
                  const v = e.target.value as 'characters' | 'locations' | 'both';
                  setSearchEntityTypes(v);
                  if (storageKey) try { localStorage.setItem(storageKey, JSON.stringify({ searchProvider, searchEntityTypes: v })); } catch { /* ignore */ }
                }}
                className="px-3 py-2 rounded-lg border border-sepia/20 font-ui text-sm text-charcoal
                           bg-white focus:border-golden focus:outline-none cursor-pointer"
              >
                {searchForOptions.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
          {!canRunSearch && totalEntities > 0 && (
            <p className="font-ui text-xs text-sepia">
              No entities match the selected type. Choose &quot;Characters & locations&quot; or the type that has entities.
            </p>
          )}
        </section>

        {characters.length > 0 && (
          <section className="space-y-3">
            <h2 className="font-display text-lg font-semibold text-charcoal flex items-center gap-2">
              <User size={18} className="text-golden" />
              Characters
            </h2>
            <div className="space-y-4">
              {characters.map((c) => (
                <EntityReviewCard
                  key={c.id}
                  name={c.name}
                  summary={c.summary}
                  queries={c.queries}
                  textToImagePrompt={c.text_to_image_prompt ?? ''}
                  onSummaryChange={(s) => setCharSummary(c.id, s)}
                  onQueriesChange={(q) => setCharQueries(c.id, q)}
                  onPromptChange={(p) => setCharPrompt(c.id, p)}
                />
              ))}
            </div>
          </section>
        )}

        {locations.length > 0 && (
          <section className="space-y-3">
            <h2 className="font-display text-lg font-semibold text-charcoal flex items-center gap-2">
              <MapPin size={18} className="text-golden" />
              Locations
            </h2>
            <div className="space-y-4">
              {locations.map((l) => (
                <EntityReviewCard
                  key={l.id}
                  name={l.name}
                  summary={l.summary}
                  queries={l.queries}
                  textToImagePrompt={l.text_to_image_prompt ?? ''}
                  onSummaryChange={(s) => setLocSummary(l.id, s)}
                  onQueriesChange={(q) => setLocQueries(l.id, q)}
                  onPromptChange={(p) => setLocPrompt(l.id, p)}
                />
              ))}
            </div>
          </section>
        )}

        {totalEntities === 0 && (
          <p className="text-sepia font-ui text-sm text-center py-8">
            No main entities selected. Go back and mark characters/locations for search.
          </p>
        )}

        {scenes.length > 0 && (
          <section className="space-y-3">
            <h2 className="font-display text-lg font-semibold text-charcoal flex items-center gap-2">
              <Film size={18} className="text-golden" />
              Scenes
              <span className="ml-auto font-ui text-xs text-sepia/60">Review & edit only</span>
            </h2>
            <p className="font-ui text-xs text-sepia/70">
              Review scene prompts before running search. Edit the draft prompt if needed.
              The AI prompt preview is read-only.
            </p>
            <div className="space-y-4">
              {scenes.map((scene) => (
                <SceneReviewCard
                  key={scene.id}
                  scene={scene}
                  onDraftChange={(draft) => handleSceneDraftChange(scene.id, draft)}
                />
              ))}
            </div>
          </section>
        )}

        <div className="flex items-center gap-4 pt-4">
          <button
            type="button"
            onClick={() => navigate(bookId ? `/books/${bookId}/analysis-review` : '/')}
            className="flex items-center gap-2 px-4 py-2.5 rounded-lg font-ui text-sm
                       text-sepia border border-sepia/20 hover:border-golden/40
                       transition-colors cursor-pointer"
          >
            <ArrowLeft size={16} />
            Back
          </button>
          <button
            type="button"
            onClick={handleRunSearch}
            disabled={running || !canRunSearch}
            className="flex-1 flex items-center justify-center gap-2 px-6 py-2.5 rounded-lg
                       font-ui font-semibold text-paper-cream bg-midnight
                       hover:bg-midnight/90 disabled:opacity-40 disabled:cursor-not-allowed
                       transition-colors shadow cursor-pointer"
          >
            {running ? (
              <>
                <Loader2 size={18} className="animate-spin" />
                Searching references...
              </>
            ) : (
              <>
                <Search size={18} />
                Run reference search
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

function SceneReviewCard({
  scene,
  onDraftChange,
}: {
  scene: ProposedScene;
  onDraftChange: (draft: string) => void;
}) {
  return (
    <div className="p-4 rounded-xl border border-sepia/15 bg-white/50 space-y-3">
      <div className="flex items-start gap-2">
        <div className="flex-1">
          <div className="flex flex-wrap items-center gap-2 mb-1">
            {(scene.title_display ?? scene.title) && (
              <h3 className="font-display font-semibold text-charcoal text-sm">
                {scene.title_display ?? scene.title}
              </h3>
            )}
            {scene.scene_type && (
              <span className="px-2 py-0.5 rounded-full bg-sepia/10 text-sepia font-ui text-xs">
                {scene.scene_type}
              </span>
            )}
            {scene.illustration_priority && (
              <span className="px-2 py-0.5 rounded-full bg-golden/10 text-golden font-ui text-xs">
                {scene.illustration_priority}
              </span>
            )}
          </div>
          {(scene.narrative_summary_display ?? scene.narrative_summary) && (
            <p className="font-body text-xs text-sepia leading-relaxed">
              {scene.narrative_summary_display ?? scene.narrative_summary}
            </p>
          )}
        </div>
      </div>
      <div>
        <label className="block font-ui text-xs text-sepia uppercase tracking-wide mb-1">
          Scene prompt draft
        </label>
        <textarea
          value={scene.scene_prompt_draft ?? ''}
          onChange={(e) => onDraftChange(e.target.value)}
          rows={2}
          className="w-full px-3 py-2 rounded-lg border border-sepia/20 font-body text-sm
                     text-charcoal placeholder-sepia/50 focus:border-golden focus:outline-none resize-none"
          placeholder="Describe the visual scene for illustration…"
        />
      </div>
      {scene.t2i_prompt_json?.abstract && (
        <div>
          <label className="block font-ui text-xs text-sepia uppercase tracking-wide mb-1">
            AI prompt preview (read-only)
          </label>
          <p className="px-3 py-2 rounded-lg bg-sepia/5 border border-sepia/10 font-body text-xs text-sepia/80 leading-relaxed">
            {scene.t2i_prompt_json.abstract}
          </p>
        </div>
      )}
    </div>
  );
}

function EntityReviewCard({
  name,
  summary,
  queries,
  textToImagePrompt,
  onSummaryChange,
  onQueriesChange,
  onPromptChange,
}: {
  name: string;
  summary: string;
  queries: string[];
  textToImagePrompt: string;
  onSummaryChange: (s: string) => void;
  onQueriesChange: (q: string[]) => void;
  onPromptChange: (p: string) => void;
}) {
  function setQueryAt(i: number, value: string) {
    const next = [...queries];
    while (next.length <= i) next.push('');
    next[i] = value;
    onQueriesChange(next);
  }
  function addQuery() {
    onQueriesChange([...queries, '']);
  }
  function removeQuery(i: number) {
    if (queries.length <= 1) return;
    onQueriesChange(queries.filter((_, j) => j !== i));
  }

  return (
    <div className="p-4 rounded-xl border border-sepia/15 bg-white/50 space-y-3">
      <h3 className="font-display font-semibold text-charcoal">{name}</h3>
      <div>
        <label className="block font-ui text-xs text-sepia uppercase tracking-wide mb-1">
          Summary
        </label>
        <textarea
          value={summary}
          onChange={(e) => onSummaryChange(e.target.value)}
          rows={2}
          className="w-full px-3 py-2 rounded-lg border border-sepia/20 font-body text-sm
                     text-charcoal placeholder-sepia/50 focus:border-golden focus:outline-none"
          placeholder="Visual description for this entity"
        />
      </div>
      <div>
        <label className="block font-ui text-xs text-sepia uppercase tracking-wide mb-1">
          Search queries (one per line)
        </label>
        <div className="space-y-2">
          {queries.map((q, i) => (
            <div key={i} className="flex gap-2">
              <input
                type="text"
                value={q}
                onChange={(e) => setQueryAt(i, e.target.value)}
                className="flex-1 px-3 py-2 rounded-lg border border-sepia/20 font-ui text-sm
                           text-charcoal placeholder-sepia/50 focus:border-golden focus:outline-none"
                placeholder={`Query ${i + 1}`}
              />
              <button
                type="button"
                onClick={() => removeQuery(i)}
                className="px-2 text-sepia hover:text-charcoal font-ui text-sm"
                disabled={queries.length <= 1}
              >
                Remove
              </button>
            </div>
          ))}
          <button
            type="button"
            onClick={addQuery}
            className="text-sm font-ui text-golden hover:underline"
          >
            + Add query
          </button>
        </div>
      </div>
      <div>
        <label className="block font-ui text-xs text-sepia uppercase tracking-wide mb-1">
          Text-to-image prompt
        </label>
        <textarea
          value={textToImagePrompt}
          onChange={(e) => onPromptChange(e.target.value)}
          rows={2}
          className="w-full px-3 py-2 rounded-lg border border-sepia/20 font-body text-sm
                     text-charcoal placeholder-sepia/50 focus:border-golden focus:outline-none"
          placeholder="e.g. core tokens, style tokens, ultra detailed, cinematic lighting"
        />
      </div>
    </div>
  );
}
