import { useEffect, useState, useRef } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Search, Loader2, ArrowLeft, User, MapPin, Film, Package, BookMarked, ChevronDown, ChevronUp, X } from 'lucide-react';
import { useBook } from '../context/BookContext';
import {
  getProposedSearchQueries,
  patchEntitySummaries,
  searchReferences,
  getCoverImages,
  getProvidersStatus,
  updateBook,
  ENABLED_PROVIDERS_STORAGE_KEY,
  type ProposedEntity,
  type ProposedScene,
  type SearchEntityTypes,
  type ProviderStatus,
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
  const [artefacts, setArtefacts] = useState<(ProposedEntity & { queries: string[] })[]>([]);
  const [coverQueries, setCoverQueries] = useState<string[]>([]);
  const [scenes, setScenes] = useState<ProposedScene[]>([]);
  const [searchProvider, setSearchProvider] = useState<'unsplash' | 'serpapi' | ''>('');
  const [searchEntityTypes, setSearchEntityTypes] = useState<SearchEntityTypes>('both');
  const [providers, setProviders] = useState<ProviderStatus[]>([]);
  const [searchEnginesOpen, setSearchEnginesOpen] = useState(false);
  const [searchQueryStrategy, setSearchQueryStrategy] = useState<'tokens' | 'adaptive'>('tokens');

  const storageKey = bookId ? `review_search_options_${bookId}` : null;

  useEffect(() => {
    if (storageKey) {
      try {
        const raw = localStorage.getItem(storageKey);
        if (raw) {
          const parsed = JSON.parse(raw) as { searchProvider?: string; searchEntityTypes?: string };
          if (parsed.searchProvider !== undefined) setSearchProvider(parsed.searchProvider as 'unsplash' | 'serpapi' | '');
          if (parsed.searchEntityTypes !== undefined) setSearchEntityTypes(parsed.searchEntityTypes as SearchEntityTypes);
        }
      } catch {
        // ignore
      }
    }
  }, [storageKey]);

  useEffect(() => {
    getProvidersStatus().then(setProviders).catch(() => {});
  }, []);

  useEffect(() => {
    if (!bookId) return;
    try {
      const raw = localStorage.getItem(`noctua_search_strategy_${bookId}`);
      if (raw === 'adaptive' || raw === 'tokens') setSearchQueryStrategy(raw);
    } catch {
      // ignore
    }
  }, [bookId]);

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
          })),
        );
        setLocations(
          data.locations.map((l) => ({
            ...l,
            queries: l.proposed_queries?.length ? [...l.proposed_queries] : [''],
          })),
        );
        setArtefacts(
          (data.artefacts ?? []).map((a) => ({
            ...a,
            queries: a.proposed_queries?.length ? [...a.proposed_queries] : [''],
          })),
        );
        setCoverQueries(data.cover?.proposed_queries?.length ? [...data.cover.proposed_queries] : ['']);
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
    const hasArtefacts = artefacts.length > 0;
    const hasCover = coverQueries.length > 0;
    const allowed: SearchEntityTypes[] = [];
    if (hasCharacters || hasLocations) {
      if (hasCharacters && hasLocations) allowed.push('both', 'characters', 'locations');
      else if (hasCharacters) allowed.push('characters');
      else allowed.push('locations');
    }
    if (hasArtefacts) allowed.push('artefacts');
    if (hasCover) allowed.push('cover');
    if (hasCharacters || hasLocations || hasArtefacts || hasCover) allowed.push('all');
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
  }, [loading, characters.length, locations.length, artefacts.length, coverQueries.length, storageKey, searchProvider]);

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
  function setArtefactQueries(id: number, queries: string[]) {
    setArtefacts((prev) =>
      prev.map((a) => (a.id === id ? { ...a, queries } : a)),
    );
  }
  function setCoverQueriesAt(queries: string[]) {
    setCoverQueries(queries);
  }

  async function handleRunSearch() {
    if (!bookId) return;
    const hasChars = characters.length > 0;
    const hasLocs = locations.length > 0;
    const hasArt = artefacts.length > 0;
    const hasCov = coverQueries.length > 0;
    const allowedSearchTypes: SearchEntityTypes[] = [];
    if (hasChars || hasLocs) {
      if (hasChars && hasLocs) allowedSearchTypes.push('both', 'characters', 'locations');
      else if (hasChars) allowedSearchTypes.push('characters');
      else allowedSearchTypes.push('locations');
    }
    if (hasArt) allowedSearchTypes.push('artefacts');
    if (hasCov) allowedSearchTypes.push('cover');
    if (hasChars || hasLocs || hasArt || hasCov) allowedSearchTypes.push('all');
    let effectiveType: SearchEntityTypes = allowedSearchTypes.includes(searchEntityTypes) ? searchEntityTypes : (allowedSearchTypes[0] ?? 'both');

    setRunning(true);
    try {
      await patchEntitySummaries(bookId, {
        characters: characters.map((c) => ({
          id: c.id,
          physical_description: c.summary || undefined,
        })),
        locations: locations.map((l) => ({
          id: l.id,
          visual_description: l.summary || undefined,
        })),
      });
      if (searchQueryStrategy) {
        await updateBook(bookId, { search_query_strategy: searchQueryStrategy });
      }

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
      const artQueries: Record<string, string[]> = {};
      artefacts.forEach((a) => {
        const qs = a.queries.map((s) => s.trim()).filter(Boolean);
        if (qs.length) artQueries[String(a.id)] = qs;
      });
      const covQueries = hasCov ? coverQueries.map((q) => q.trim()).filter(Boolean) : undefined;
      const refs = await searchReferences(bookId, true, {
        character_queries: charQueries,
        location_queries: locQueries,
        ...(Object.keys(artQueries).length ? { artefact_queries: artQueries } : {}),
        ...(covQueries?.length ? { cover_queries: covQueries } : {}),
        ...(preferredProvider ? { preferred_provider: preferredProvider } : {}),
        search_entity_types: effectiveType,
        ...(enabledProviders ? { enabled_providers: enabledProviders } : {}),
      });
      const prev = ctx.referenceImages;
      ctx.setReferenceImages({
        characters: (effectiveType === 'locations' || effectiveType === 'artefacts' || effectiveType === 'cover') && prev?.characters ? prev.characters : (refs.characters ?? {}),
        locations: (effectiveType === 'characters' || effectiveType === 'artefacts' || effectiveType === 'cover') && prev?.locations ? prev.locations : (refs.locations ?? {}),
        artefacts: (effectiveType !== 'artefacts' && effectiveType !== 'all') && prev?.artefacts ? prev.artefacts : (refs.artefacts ?? {}),
        cover: (effectiveType !== 'cover' && effectiveType !== 'all') && prev?.cover ? prev.cover : (refs.cover ?? undefined),
      });
      if (storageKey) {
        try {
          localStorage.setItem(storageKey, JSON.stringify({ searchProvider, searchEntityTypes: effectiveType }));
        } catch {
          // ignore
        }
      }
      const initialTab =
        effectiveType === 'locations' ? 'locations'
        : effectiveType === 'artefacts' ? 'artefacts'
        : effectiveType === 'cover' ? 'cover'
        : 'characters';
      const coverForPass = (effectiveType !== 'cover' && effectiveType !== 'all') && prev?.cover ? prev.cover : refs.cover;
      const refsToPass = {
        characters: (effectiveType === 'locations' || effectiveType === 'artefacts' || effectiveType === 'cover') && prev?.characters ? prev.characters : (refs.characters ?? {}),
        locations: (effectiveType === 'characters' || effectiveType === 'artefacts' || effectiveType === 'cover') && prev?.locations ? prev.locations : (refs.locations ?? {}),
        artefacts: (effectiveType !== 'artefacts' && effectiveType !== 'all') && prev?.artefacts ? prev.artefacts : (refs.artefacts ?? {}),
        cover: coverForPass ? { cover: getCoverImages({ cover: coverForPass }) } : undefined,
      };
      navigate(bookId ? `/books/${bookId}/review-search-result` : '/review-search-result', { state: { initialTab, referenceImages: refsToPass } });
    } catch (err) {
      console.error('Search failed', err);
      alert('Reference image search failed. Please try again.');
    } finally {
      setRunning(false);
    }
  }

  function handleSearchStrategyChange(value: 'tokens' | 'adaptive') {
    setSearchQueryStrategy(value);
    if (bookId) {
      try {
        localStorage.setItem(`noctua_search_strategy_${bookId}`, value);
      } catch {
        // ignore
      }
      updateBook(bookId, { search_query_strategy: value }).catch(console.error);
    }
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
  const hasArtefacts = artefacts.length > 0;
  const hasCover = coverQueries.length > 0;
  const searchForOptions: Array<{ value: SearchEntityTypes; label: string }> = [];
  if (hasCharacters && hasLocations) {
    searchForOptions.push({ value: 'both', label: 'Characters & locations' }, { value: 'characters', label: 'Characters only' }, { value: 'locations', label: 'Locations only' });
  } else if (hasCharacters) searchForOptions.push({ value: 'characters', label: 'Characters only' });
  else if (hasLocations) searchForOptions.push({ value: 'locations', label: 'Locations only' });
  if (hasArtefacts) searchForOptions.push({ value: 'artefacts', label: 'Artefacts only' });
  if (hasCover) searchForOptions.push({ value: 'cover', label: 'Cover only' });
  if (hasCharacters || hasLocations || hasArtefacts || hasCover) searchForOptions.push({ value: 'all', label: 'All (characters, locations, artefacts, cover)' });

  const effectiveSearchEntityTypes = searchForOptions.some((o) => o.value === searchEntityTypes) ? searchEntityTypes : (searchForOptions[0]?.value ?? 'both');
  const totalEntities = characters.length + locations.length + artefacts.length + (hasCover ? 1 : 0);
  const searchableCount =
    effectiveSearchEntityTypes === 'both' ? characters.length + locations.length
    : effectiveSearchEntityTypes === 'characters' ? characters.length
    : effectiveSearchEntityTypes === 'locations' ? locations.length
    : effectiveSearchEntityTypes === 'artefacts' ? artefacts.length
    : effectiveSearchEntityTypes === 'cover' ? (hasCover ? 1 : 0)
    : totalEntities;
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
            Edit the AI summary and reference image search queries per entity. Then run the search.
          </p>
        </div>

        {/* Search Engines panel (7.7.3) — collapsible */}
        <section className="p-4 rounded-xl border border-sepia/15 bg-white/50 space-y-3">
          <button
            type="button"
            onClick={() => setSearchEnginesOpen((o) => !o)}
            className="flex items-center gap-2 w-full text-left font-display text-sm font-semibold text-charcoal"
          >
            {searchEnginesOpen ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
            Search engines for this session
          </button>
          {searchEnginesOpen && (
            <>
              <p className="font-ui text-xs text-sepia/70">
                Changes here apply to the current search only. Default engines are set in Settings.
              </p>
              <div className="flex flex-wrap gap-2">
                {providers.map((p) => {
                  let enabled: string[] = [];
                  try {
                    const raw = localStorage.getItem(ENABLED_PROVIDERS_STORAGE_KEY);
                    if (raw) {
                      const parsed = JSON.parse(raw);
                      if (Array.isArray(parsed)) enabled = parsed;
                    }
                  } catch {
                    // ignore
                  }
                  const isOn = enabled.length === 0 ? true : enabled.includes(p.name);
                  const toggle = () => {
                    const next = isOn ? enabled.filter((x) => x !== p.name) : [...enabled, p.name];
                    const toStore = next.length > 0 ? next : providers.map((x) => x.name);
                    try {
                      localStorage.setItem(ENABLED_PROVIDERS_STORAGE_KEY, JSON.stringify(toStore));
                    } catch {
                      // ignore
                    }
                    setProviders([...providers]);
                  };
                  return (
                    <button
                      key={p.name}
                      type="button"
                      onClick={toggle}
                      className={`px-3 py-1.5 rounded-full font-ui text-xs border transition-colors ${
                        isOn ? 'bg-golden/20 border-golden text-charcoal' : 'border-sepia/20 text-sepia'
                      }`}
                    >
                      {p.label}
                    </button>
                  );
                })}
              </div>
              <div className="pt-2 border-t border-sepia/10">
                <span className="block font-ui text-xs text-sepia uppercase tracking-wide mb-2">Query strategy</span>
                <div className="flex gap-4">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input type="radio" name="strategy" checked={searchQueryStrategy === 'tokens'} onChange={() => handleSearchStrategyChange('tokens')} className="rounded-full" />
                    <span className="font-ui text-sm">Compact keywords</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input type="radio" name="strategy" checked={searchQueryStrategy === 'adaptive'} onChange={() => handleSearchStrategyChange('adaptive')} className="rounded-full" />
                    <span className="font-ui text-sm">Adaptive</span>
                  </label>
                </div>
                <p className="font-ui text-[10px] text-sepia/70 mt-1">Compact = same tokens for all engines. Adaptive = sentences for Google, keywords for tag-based.</p>
              </div>
            </>
          )}
        </section>

        {/* Search options */}
        <section className="p-4 rounded-xl border border-sepia/15 bg-white/50 space-y-4">
          <h2 className="font-display text-sm font-semibold text-charcoal uppercase tracking-wide">
            Search options
          </h2>
          <div className="flex flex-wrap gap-6">
            <div className="space-y-2">
              <label className="block font-ui text-xs text-sepia">Preferred provider</label>
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
                  const v = e.target.value as SearchEntityTypes;
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
                  onSummaryChange={(s) => setCharSummary(c.id, s)}
                  onQueriesChange={(q) => setCharQueries(c.id, q)}
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
                  onSummaryChange={(s) => setLocSummary(l.id, s)}
                  onQueriesChange={(q) => setLocQueries(l.id, q)}
                />
              ))}
            </div>
          </section>
        )}

        {artefacts.length > 0 && (
          <section className="space-y-3">
            <h2 className="font-display text-lg font-semibold text-charcoal flex items-center gap-2">
              <Package size={18} className="text-golden" />
              Artefacts
            </h2>
            <div className="space-y-4">
              {artefacts.map((a) => (
                <EntityReviewCard
                  key={a.id}
                  name={a.name}
                  summary={a.summary}
                  queries={a.queries}
                  onSummaryChange={() => {}}
                  onQueriesChange={(q) => setArtefactQueries(a.id, q)}
                />
              ))}
            </div>
          </section>
        )}

        {coverQueries.length > 0 && (
          <section className="space-y-3">
            <h2 className="font-display text-lg font-semibold text-charcoal flex items-center gap-2">
              <BookMarked size={18} className="text-golden" />
              Cover
            </h2>
            <p className="font-ui text-xs text-sepia/70">Proposed search queries for cover concept.</p>
            <div className="space-y-2">
              {coverQueries.map((q, i) => (
                <div key={i} className="flex gap-2">
                  <input
                    type="text"
                    value={q}
                    onChange={(e) =>
                      setCoverQueries((prev) => {
                        const next = [...prev];
                        next[i] = e.target.value;
                        return next;
                      })
                    }
                    placeholder="e.g. dark fantasy book cover"
                    className="flex-1 px-3 py-2 rounded-lg border border-sepia/20 font-ui text-sm text-charcoal bg-white focus:outline-none focus:ring-2 focus:ring-golden/40"
                  />
                  <button
                    type="button"
                    onClick={() => coverQueries.length > 1 && setCoverQueries((prev) => prev.filter((_, j) => j !== i))}
                    disabled={coverQueries.length <= 1}
                    className="px-2 text-sepia hover:text-charcoal disabled:opacity-40 font-ui text-sm"
                    aria-label="Remove query"
                  >
                    <X size={18} />
                  </button>
                </div>
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
              <span className="ml-auto font-ui text-xs text-sepia/60">Read-only reference</span>
            </h2>
            <p className="font-ui text-xs text-sepia/70">
              Scene list for context. T2I prompts are edited in Cover Studio / Text Studio.
            </p>
            <div className="space-y-4">
              {scenes.map((scene) => (
                <SceneReviewCard key={scene.id} scene={scene} />
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

function SceneReviewCard({ scene }: { scene: ProposedScene }) {
  return (
    <div className="p-4 rounded-xl border border-sepia/15 bg-white/50 space-y-3">
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
  onSummaryChange,
  onQueriesChange,
}: {
  name: string;
  summary: string;
  queries: string[];
  onSummaryChange: (s: string) => void;
  onQueriesChange: (q: string[]) => void;
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
    </div>
  );
}
