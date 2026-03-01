import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Users, MapPin, Film, Search, Loader2, ArrowLeft, Star, ChevronDown, ChevronUp, Tag, Sparkles, Package, Bookmark, Palette, Pencil, X } from 'lucide-react';
import { useBook } from '../context/BookContext';
import {
  getCharacters,
  getLocations,
  getScenes,
  getArtefacts,
  getCoverAnalysis,
  updateCoverAnalysis,
  updateEntitySelections,
  patchEntitySummaries,
  updateArtefact,
  updateScene,
  analyzeEntity,
  type Character,
  type Location,
  type SceneResponse,
  type Artefact,
  type CoverAnalysisResponse,
} from '../services/api';

type Tab = 'characters' | 'locations' | 'scenes' | 'artefacts' | 'cover' | 'style';

export default function AnalysisReviewPage() {
  const navigate = useNavigate();
  const ctx = useBook();

  const [activeTab, setActiveTab] = useState<Tab>('characters');
  const [characters, setCharacters] = useState<Character[]>([]);
  const [locations, setLocations] = useState<Location[]>([]);
  const [scenes, setScenes] = useState<SceneResponse[]>([]);
  const [artefacts, setArtefacts] = useState<Artefact[]>([]);
  const [coverAnalysis, setCoverAnalysis] = useState<CoverAnalysisResponse | null>(null);
  const [charMainFlags, setCharMainFlags] = useState<Record<number, boolean>>({});
  const [locMainFlags, setLocMainFlags] = useState<Record<number, boolean>>({});
  const [artefactMainFlags, setArtefactMainFlags] = useState<Record<number, boolean>>({});
  const [loading, setLoading] = useState(true);
  const [searching, setSearching] = useState(false);
  const [reanalyzing, setReanalyzing] = useState<string | null>(null);
  const [editingEntityId, setEditingEntityId] = useState<string | null>(null);
  const [editDraft, setEditDraft] = useState<Record<string, string> | null>(null);
  const [editError, setEditError] = useState<string | null>(null);

  useEffect(() => {
    if (!ctx.book) {
      navigate('/');
      return;
    }

    async function load() {
      try {
        const [chars, locs, scns, arts, cover] = await Promise.all([
          getCharacters(ctx.book!.id),
          getLocations(ctx.book!.id),
          getScenes(ctx.book!.id).catch(() => []),
          getArtefacts(ctx.book!.id).catch(() => []),
          getCoverAnalysis(ctx.book!.id).catch(() => null),
        ]);
        setCharacters(chars);
        setLocations(locs);
        setScenes(scns);
        setArtefacts(arts);
        setCoverAnalysis(cover);

        const cFlags: Record<number, boolean> = {};
        for (const c of chars) cFlags[c.id] = c.is_main === 1;
        setCharMainFlags(cFlags);

        const lFlags: Record<number, boolean> = {};
        for (const l of locs) lFlags[l.id] = l.is_main === 1;
        setLocMainFlags(lFlags);

        const aFlags: Record<number, boolean> = {};
        for (const a of arts) aFlags[a.id] = a.is_main === 1;
        setArtefactMainFlags(aFlags);
      } catch (err) {
        console.error('Failed to load analysis results', err);
      } finally {
        setLoading(false);
      }
    }

    load();
  }, [ctx.book, navigate]);

  function toggleChar(id: number) {
    setCharMainFlags((prev) => ({ ...prev, [id]: !prev[id] }));
  }

  function toggleLoc(id: number) {
    setLocMainFlags((prev) => ({ ...prev, [id]: !prev[id] }));
  }

  function toggleArtefact(id: number) {
    setArtefactMainFlags((prev) => ({ ...prev, [id]: !prev[id] }));
  }

  const handleToggleScene = useCallback(async (sceneId: number) => {
    if (!ctx.book) return;
    const scene = scenes.find((s) => s.id === sceneId);
    if (!scene) return;
    const newVal = !scene.is_selected;
    setScenes((prev) =>
      prev.map((s) => (s.id === sceneId ? { ...s, is_selected: newVal } : s)),
    );
    try {
      await updateScene(ctx.book.id, sceneId, { is_selected: newVal });
    } catch (err) {
      console.error('Failed to update scene selection', err);
      setScenes((prev) =>
        prev.map((s) => (s.id === sceneId ? { ...s, is_selected: !newVal } : s)),
      );
    }
  }, [ctx.book, scenes]);

  const handleUpdateScene = useCallback(async (sceneId: number, updates: { title?: string; narrative_summary?: string; dramatic_score_avg?: number }) => {
    if (!ctx.book) return;
    try {
      const updated = await updateScene(ctx.book.id, sceneId, updates);
      setScenes((prev) => prev.map((s) => (s.id === sceneId ? { ...s, ...updated } : s)));
    } catch (err) {
      console.error('Failed to save scene', err);
    }
  }, [ctx.book]);

  const selectedCharCount = Object.values(charMainFlags).filter(Boolean).length;
  const selectedLocCount = Object.values(locMainFlags).filter(Boolean).length;
  const selectedArtefactCount = Object.values(artefactMainFlags).filter(Boolean).length;
  const selectedSceneCount = scenes.filter((s) => s.is_selected).length;

  async function handleReanalyzeEntity(entityType: string) {
    if (!ctx.book) return;
    setReanalyzing(entityType);
    try {
      await analyzeEntity(ctx.book.id, entityType);
      alert(`Re-analysis started for ${entityType}. You can leave this page; check back in a few minutes.`);
    } catch (err) {
      console.error('Re-analyze failed', err);
      alert('Failed to start re-analysis. Please try again.');
    } finally {
      setReanalyzing(null);
    }
  }

  async function handlePrepareSearch() {
    if (!ctx.book) return;
    setSearching(true);
    try {
      await updateEntitySelections(ctx.book.id, {
        characters: characters.map((c) => ({
          id: c.id,
          is_main: !!charMainFlags[c.id],
        })),
        locations: locations.map((l) => ({
          id: l.id,
          is_main: !!locMainFlags[l.id],
        })),
        artefacts: artefacts.map((a) => ({
          id: a.id,
          is_main: !!artefactMainFlags[a.id],
        })),
      });
      navigate(`/books/${ctx.book.id}/review-search`);
    } catch (err) {
      console.error('Failed to save selections', err);
      alert('Failed to save. Please try again.');
    } finally {
      setSearching(false);
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-paper-cream flex items-center justify-center">
        <Loader2 size={32} className="animate-spin text-golden" />
      </div>
    );
  }

  const TABS: { id: Tab; label: string; count: number; icon: typeof Users }[] = [
    { id: 'characters', label: 'Characters', count: selectedCharCount, icon: Users },
    { id: 'locations', label: 'Locations', count: selectedLocCount, icon: MapPin },
    { id: 'artefacts', label: 'Artefacts', count: selectedArtefactCount, icon: Package },
    { id: 'scenes', label: 'Scenes', count: selectedSceneCount, icon: Film },
    { id: 'cover', label: 'Cover / Title', count: coverAnalysis ? 1 : 0, icon: Bookmark },
    { id: 'style', label: 'Style', count: coverAnalysis ? 1 : 0, icon: Palette },
  ];

  return (
    <div className="min-h-screen bg-paper-cream px-4 py-12">
      <div className="max-w-3xl mx-auto space-y-8">
        {/* Header */}
        <div className="text-center space-y-2">
          <h1 className="font-display text-3xl font-semibold text-charcoal">
            Analysis Results
          </h1>
          <p className="text-sepia font-body text-sm">{ctx.book?.title}</p>
          <p className="text-sepia/70 font-ui text-xs max-w-lg mx-auto">
            Review AI-identified characters, locations, and scenes. Toggle the star to mark
            entities for reference search. Toggle scenes to select which ones to illustrate.
          </p>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-sepia/20 gap-1">
          {TABS.map(({ id, label, count, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setActiveTab(id)}
              className={`flex items-center gap-2 px-4 py-2.5 font-ui text-sm transition-colors
                cursor-pointer border-b-2 -mb-px
                ${activeTab === id
                  ? 'border-golden text-charcoal font-semibold'
                  : 'border-transparent text-sepia hover:text-charcoal'}`}
            >
              <Icon size={16} />
              {label}
              <span className={`text-xs px-1.5 py-0.5 rounded-full ${activeTab === id ? 'bg-golden/20 text-golden' : 'bg-sepia/10 text-sepia'}`}>
                {count}
              </span>
            </button>
          ))}
        </div>

        {/* Characters tab */}
        {activeTab === 'characters' && (
          <section className="space-y-3">
            <p className="font-ui text-xs text-sepia/70">
              {selectedCharCount} selected for reference image search
            </p>
            <div className="grid gap-3">
              {characters.map((c) => (
                <CharacterCard
                  key={c.id}
                  character={c}
                  isMain={!!charMainFlags[c.id]}
                  onToggle={() => toggleChar(c.id)}
                  isEditing={editingEntityId === `char-${c.id}`}
                  editDraft={editingEntityId === `char-${c.id}` ? editDraft : null}
                  onEdit={() => {
                    setEditingEntityId(`char-${c.id}`);
                    setEditDraft({
                      name: c.name,
                      physical_description: c.physical_description ?? '',
                      full_description: (c as Character & { full_description?: string | null }).full_description ?? '',
                      personality_traits: c.personality_traits ?? '',
                    });
                    setEditError(null);
                  }}
                  onSave={async (data) => {
                    if (!ctx.book) return;
                    setEditError(null);
                    try {
                      await patchEntitySummaries(ctx.book.id, {
                        characters: [{ id: c.id, ...data }],
                        locations: [],
                      });
                      setCharacters((prev) => prev.map((x) => (x.id === c.id ? { ...x, ...data } : x)));
                      setEditingEntityId(null);
                      setEditDraft(null);
                    } catch (err) {
                      setEditError('Failed to save. Please try again.');
                    }
                  }}
                  onCancel={() => { setEditingEntityId(null); setEditDraft(null); setEditError(null); }}
                  onDraftChange={(key, value) => setEditDraft((p) => (p ? { ...p, [key]: value } : null))}
                  editError={editingEntityId === `char-${c.id}` ? editError : null}
                />
              ))}
            </div>
          </section>
        )}

        {/* Locations tab */}
        {activeTab === 'locations' && (
          <section className="space-y-3">
            <p className="font-ui text-xs text-sepia/70">
              {selectedLocCount} selected for reference image search
            </p>
            <div className="grid gap-3">
              {locations.map((l) => (
                <LocationCard
                  key={l.id}
                  location={l}
                  isMain={!!locMainFlags[l.id]}
                  onToggle={() => toggleLoc(l.id)}
                  isEditing={editingEntityId === `loc-${l.id}`}
                  editDraft={editingEntityId === `loc-${l.id}` ? editDraft : null}
                  onEdit={() => {
                    setEditingEntityId(`loc-${l.id}`);
                    setEditDraft({
                      name: l.name,
                      visual_description: l.visual_description ?? '',
                      full_description: (l as Location & { full_description?: string | null }).full_description ?? '',
                      atmosphere: l.atmosphere ?? '',
                    });
                    setEditError(null);
                  }}
                  onSave={async (data) => {
                    if (!ctx.book) return;
                    setEditError(null);
                    try {
                      await patchEntitySummaries(ctx.book.id, {
                        characters: [],
                        locations: [{ id: l.id, ...data }],
                      });
                      setLocations((prev) => prev.map((x) => (x.id === l.id ? { ...x, ...data } : x)));
                      setEditingEntityId(null);
                      setEditDraft(null);
                    } catch (err) {
                      setEditError('Failed to save. Please try again.');
                    }
                  }}
                  onCancel={() => { setEditingEntityId(null); setEditDraft(null); setEditError(null); }}
                  onDraftChange={(key, value) => setEditDraft((p) => (p ? { ...p, [key]: value } : null))}
                  editError={editingEntityId === `loc-${l.id}` ? editError : null}
                />
              ))}
            </div>
          </section>
        )}

        {/* Scenes tab */}
        {activeTab === 'scenes' && (
          <section className="space-y-3">
            <p className="font-ui text-xs text-sepia/70">
              {selectedSceneCount} of {scenes.length} scenes selected for illustration
            </p>
            {scenes.length === 0 ? (
              <p className="text-sepia font-ui text-sm text-center py-8">
                No scenes extracted yet. Run analysis first.
              </p>
            ) : (
              <div className="grid gap-4">
                {scenes.map((scene) => (
                  <SceneCard
                    key={scene.id}
                    scene={scene}
                    onToggleSelected={() => handleToggleScene(scene.id)}
                    onSave={(updates) => handleUpdateScene(scene.id, updates)}
                  />
                ))}
              </div>
            )}
          </section>
        )}

        {/* Artefacts tab */}
        {activeTab === 'artefacts' && (
          <section className="space-y-3">
            <p className="font-ui text-xs text-sepia/70">
              {selectedArtefactCount} selected for reference image search. Toggle the star to include in search.
            </p>
            {artefacts.length === 0 ? (
              <p className="text-sepia font-ui text-sm text-center py-8">
                No artefacts extracted yet. Run analysis with Artefacts enabled.
              </p>
            ) : (
              <div className="grid gap-3">
                {artefacts.map((a) => (
                  <ArtefactCard
                    key={a.id}
                    artefact={a}
                    isMain={!!artefactMainFlags[a.id]}
                    onToggle={() => toggleArtefact(a.id)}
                    isEditing={editingEntityId === `art-${a.id}`}
                    editDraft={editingEntityId === `art-${a.id}` ? editDraft : null}
                    onEdit={() => {
                      setEditingEntityId(`art-${a.id}`);
                      setEditDraft({
                        name: a.name,
                        physical_description: a.physical_description ?? '',
                        full_description: a.full_description ?? '',
                        symbolic_role: a.symbolic_role ?? '',
                      });
                      setEditError(null);
                    }}
                    onSave={async (data) => {
                      if (!ctx.book) return;
                      setEditError(null);
                      try {
                        await updateArtefact(ctx.book.id, a.id, data);
                        setArtefacts((prev) => prev.map((x) => (x.id === a.id ? { ...x, ...data } : x)));
                        setEditingEntityId(null);
                        setEditDraft(null);
                      } catch (err) {
                        setEditError('Failed to save. Please try again.');
                      }
                    }}
                    onCancel={() => { setEditingEntityId(null); setEditDraft(null); setEditError(null); }}
                    onDraftChange={(key, value) => setEditDraft((p) => (p ? { ...p, [key]: value } : null))}
                    editError={editingEntityId === `art-${a.id}` ? editError : null}
                  />
                ))}
              </div>
            )}
          </section>
        )}

        {/* Cover / Title analysis tab (7.6.2 editable) */}
        {activeTab === 'cover' && (
          <CoverTab
            coverAnalysis={coverAnalysis}
            onSave={async (data) => {
              if (!ctx.book) return;
              const updated = await updateCoverAnalysis(ctx.book.id, data);
              setCoverAnalysis(updated);
            }}
          />
        )}

        {/* Style tab (7.6.4) — moved from VisualBibleReview */}
        {activeTab === 'style' && (
          <StyleTab
            coverAnalysis={coverAnalysis}
            onSave={async (data) => {
              if (!ctx.book) return;
              const updated = await updateCoverAnalysis(ctx.book.id, data);
              setCoverAnalysis(updated);
            }}
          />
        )}

        {/* Re-analyze by entity type */}
        <section className="p-4 rounded-xl border border-sepia/15 bg-white/50 space-y-2">
          <h3 className="font-display text-sm font-semibold text-charcoal">Re-run analysis (single type)</h3>
          <p className="font-ui text-xs text-sepia/70">
            Re-analyze only one entity type without touching the rest. Useful to fix or refresh characters, locations, artefacts, or cover.
          </p>
          <div className="flex flex-wrap gap-2">
            {(['characters', 'locations', 'artefacts', 'cover'] as const).map((et) => (
              <button
                key={et}
                onClick={() => handleReanalyzeEntity(et)}
                disabled={!!reanalyzing}
                className="px-3 py-1.5 rounded-lg font-ui text-sm border border-sepia/20
                         text-charcoal hover:border-golden/40 hover:bg-golden/5
                         disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {reanalyzing === et ? (
                  <>
                    <Loader2 size={14} className="inline animate-spin mr-1" />
                    Starting…
                  </>
                ) : (
                  et.charAt(0).toUpperCase() + et.slice(1)
                )}
              </button>
            ))}
          </div>
        </section>

        {/* Actions */}
        <div className="flex items-center gap-4 pt-4">
          <button
            onClick={() => navigate(ctx.book ? `/books/${ctx.book.id}/manuscript-upload` : '/manuscript-upload')}
            className="flex items-center gap-2 px-4 py-2.5 rounded-lg font-ui text-sm
                       text-sepia border border-sepia/20 hover:border-golden/40
                       transition-colors cursor-pointer"
          >
            <ArrowLeft size={16} />
            Back
          </button>

          <button
            onClick={handlePrepareSearch}
            disabled={searching || (selectedCharCount === 0 && selectedLocCount === 0 && selectedArtefactCount === 0)}
            className="flex-1 flex items-center justify-center gap-2 px-6 py-2.5 rounded-lg
                       font-ui font-semibold text-paper-cream bg-midnight
                       hover:bg-midnight/90 disabled:opacity-40 disabled:cursor-not-allowed
                       transition-colors shadow cursor-pointer"
          >
            {searching ? (
              <>
                <Loader2 size={18} className="animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Search size={18} />
                Prepare reference search ({selectedCharCount + selectedLocCount + selectedArtefactCount} entities)
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

function EntitySection({
  title,
  children,
  defaultOpen = false,
}: {
  title: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="border-t border-sepia/10 pt-2 mt-2 first:border-t-0 first:pt-0 first:mt-0">
      <button
        type="button"
        onClick={(e) => { e.stopPropagation(); setOpen((o) => !o); }}
        className="flex items-center gap-1 w-full text-left font-ui text-xs font-medium text-sepia hover:text-charcoal"
      >
        {open ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        {title}
      </button>
      {open && <div className="mt-1.5 space-y-1">{children}</div>}
    </div>
  );
}

/** Cover tab (7.6.2): editable thematic_statement, mood_keywords, visual_style_tags, cover_t2i_prompt, cover_type, color_palette_structured, full_description. */
function CoverTab({
  coverAnalysis,
  onSave,
}: {
  coverAnalysis: CoverAnalysisResponse | null;
  onSave: (data: Record<string, unknown>) => Promise<void>;
}) {
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [thematic, setThematic] = useState('');
  const [emotional, setEmotional] = useState('');
  const [moodCsv, setMoodCsv] = useState('');
  const [t2iPrompt, setT2iPrompt] = useState('');
  const [coverType, setCoverType] = useState('');
  const [fullDesc, setFullDesc] = useState('');
  const [colorPalette, setColorPalette] = useState<Record<string, string>>({});

  useEffect(() => {
    if (!coverAnalysis) return;
    setThematic(coverAnalysis.thematic_statement ?? '');
    setEmotional(coverAnalysis.emotional_promise ?? '');
    setMoodCsv(Array.isArray(coverAnalysis.cover_mood_keywords) ? coverAnalysis.cover_mood_keywords.join(', ') : '');
    setT2iPrompt(coverAnalysis.cover_t2i_prompt ?? '');
    setCoverType((coverAnalysis as Record<string, string>).cover_type ?? '');
    setFullDesc((coverAnalysis as Record<string, string>).full_description ?? '');
    const cp = coverAnalysis.color_palette_structured;
    if (cp && typeof cp === 'object') setColorPalette((cp as Record<string, string>) || {});
    else setColorPalette({});
  }, [coverAnalysis]);

  if (!coverAnalysis) {
    return (
      <section className="space-y-3">
        <p className="text-sepia font-ui text-sm text-center py-8">
          No cover/title analysis yet. Run analysis with Cover enabled.
        </p>
      </section>
    );
  }

  async function handleSave() {
    setSaving(true);
    try {
      await onSave({
        thematic_statement: thematic || undefined,
        emotional_promise: emotional || undefined,
        cover_mood_keywords: moodCsv.split(',').map((s) => s.trim()).filter(Boolean),
        cover_t2i_prompt: t2iPrompt || undefined,
        cover_type: coverType || undefined,
        full_description: fullDesc || undefined,
        color_palette_structured: Object.keys(colorPalette).length ? colorPalette : undefined,
      });
      setEditing(false);
    } catch (err) {
      console.error('Failed to save cover', err);
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="space-y-3">
      <div className="space-y-4 p-4 rounded-xl border border-sepia/15 bg-white/50">
        <div className="flex justify-end gap-2">
          {!editing ? (
            <button type="button" onClick={() => setEditing(true)} className="px-3 py-1.5 rounded-lg font-ui text-xs border border-sepia/20 text-charcoal hover:border-golden/40">Edit</button>
          ) : (
            <>
              <button type="button" onClick={() => setEditing(false)} className="px-3 py-1.5 rounded font-ui text-xs border border-sepia/20">Cancel</button>
              <button type="button" onClick={handleSave} disabled={saving} className="px-3 py-1.5 rounded font-ui text-xs bg-golden text-charcoal disabled:opacity-50">{saving ? 'Saving...' : 'Save'}</button>
            </>
          )}
        </div>
        <div className="space-y-4">
          <div>
            <h4 className="font-ui text-xs font-semibold text-charcoal mb-1">Thematic statement</h4>
            {editing ? <textarea value={thematic} onChange={(e) => setThematic(e.target.value)} rows={2} className="w-full px-3 py-2 rounded-lg border border-sepia/20 text-sm" /> : <p className="font-body text-sm text-sepia">{thematic || '—'}</p>}
          </div>
          <div>
            <h4 className="font-ui text-xs font-semibold text-charcoal mb-1">Emotional promise</h4>
            {editing ? <textarea value={emotional} onChange={(e) => setEmotional(e.target.value)} rows={2} className="w-full px-3 py-2 rounded-lg border border-sepia/20 text-sm" /> : <p className="font-body text-sm text-sepia">{emotional || '—'}</p>}
          </div>
          <div>
            <h4 className="font-ui text-xs font-semibold text-charcoal mb-1">Cover mood (comma-separated)</h4>
            {editing ? <input type="text" value={moodCsv} onChange={(e) => setMoodCsv(e.target.value)} className="w-full px-3 py-2 rounded-lg border border-sepia/20 text-sm" /> : <p className="font-body text-sm text-sepia">{moodCsv || '—'}</p>}
          </div>
          <div>
            <h4 className="font-ui text-xs font-semibold text-charcoal mb-1">Cover image prompt</h4>
            {editing ? <textarea value={t2iPrompt} onChange={(e) => setT2iPrompt(e.target.value)} rows={3} className="w-full px-3 py-2 rounded-lg border border-sepia/20 text-sm whitespace-pre-wrap" /> : <p className="font-body text-sm text-sepia whitespace-pre-wrap">{t2iPrompt || '—'}</p>}
          </div>
          <div>
            <h4 className="font-ui text-xs font-semibold text-charcoal mb-1">Cover type</h4>
            {editing ? (
              <select value={coverType} onChange={(e) => setCoverType(e.target.value)} className="px-3 py-2 rounded-lg border border-sepia/20 text-sm">
                <option value="">—</option>
                <option value="object_centered">Object centered</option>
                <option value="character_centered">Character centered</option>
                <option value="setting_centered">Setting centered</option>
                <option value="abstract">Abstract</option>
                <option value="typography_centered">Typography centered</option>
              </select>
            ) : (
              <p className="font-body text-sm text-sepia">{coverType || '—'}</p>
            )}
          </div>
          <div>
            <h4 className="font-ui text-xs font-semibold text-charcoal mb-1">Full description</h4>
            {editing ? <textarea value={fullDesc} onChange={(e) => setFullDesc(e.target.value)} rows={2} className="w-full px-3 py-2 rounded-lg border border-sepia/20 text-sm" /> : <p className="font-body text-sm text-sepia">{fullDesc || '—'}</p>}
          </div>
          {coverAnalysis.genre_conventions && !editing && (
            <div>
              <h4 className="font-ui text-xs font-semibold text-charcoal mb-1">Genre conventions</h4>
              <p className="font-body text-sm text-sepia">{coverAnalysis.genre_conventions}</p>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

/** Style tab (7.6.4): visual_style_tags (typography/genre), mood_keywords, color_palette_structured, thematic_statement — editable, Save calls updateCoverAnalysis. */
function StyleTab({
  coverAnalysis,
  onSave,
}: {
  coverAnalysis: CoverAnalysisResponse | null;
  onSave: (data: Record<string, unknown>) => Promise<void>;
}) {
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [thematic, setThematic] = useState('');
  const [moodCsv, setMoodCsv] = useState('');
  const [styleTagsCsv, setStyleTagsCsv] = useState('');
  const [colorPalette, setColorPalette] = useState<{ dominant?: string; accent?: string; temperature?: string; contrast?: string; saturation?: string }>({});

  useEffect(() => {
    if (!coverAnalysis) return;
    setThematic(coverAnalysis.thematic_statement ?? '');
    setMoodCsv(Array.isArray(coverAnalysis.cover_mood_keywords) ? coverAnalysis.cover_mood_keywords.join(', ') : (coverAnalysis.cover_mood_keywords ?? ''));
    const dir = coverAnalysis.typography_direction ?? '';
    const genre = coverAnalysis.genre_conventions ?? '';
    setStyleTagsCsv([dir, genre].filter(Boolean).join(', '));
    const cp = coverAnalysis.color_palette_structured;
    if (cp && typeof cp === 'object') {
      setColorPalette({
        dominant: (cp as Record<string, string>).dominant ?? '',
        accent: (cp as Record<string, string>).accent ?? '',
        temperature: (cp as Record<string, string>).temperature ?? '',
        contrast: (cp as Record<string, string>).contrast ?? '',
        saturation: (cp as Record<string, string>).saturation ?? '',
      });
    } else {
      setColorPalette({});
    }
  }, [coverAnalysis]);

  if (!coverAnalysis) {
    return (
      <section className="space-y-3">
        <p className="text-sepia font-ui text-sm text-center py-8">
          No cover analysis yet. Run analysis with Cover enabled to see style summary.
        </p>
      </section>
    );
  }

  async function handleSave() {
    setSaving(true);
    try {
      const moodKeywords = moodCsv.split(',').map((s) => s.trim()).filter(Boolean);
      const visualStyleTags = styleTagsCsv.split(',').map((s) => s.trim()).filter(Boolean);
      await onSave({
        thematic_statement: thematic || undefined,
        cover_mood_keywords: moodKeywords.length ? moodKeywords : undefined,
        typography_direction: visualStyleTags[0] ?? undefined,
        genre_conventions: visualStyleTags.slice(1).join(', ') || undefined,
        color_palette_structured: Object.keys(colorPalette).length ? colorPalette : undefined,
      });
      setEditing(false);
    } catch (err) {
      console.error('Failed to save style', err);
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="space-y-4 p-4 rounded-xl border border-sepia/15 bg-white/50">
      <div className="flex items-center justify-between">
        <h3 className="font-display text-sm font-semibold text-charcoal">Style summary</h3>
        {!editing ? (
          <button
            type="button"
            onClick={() => setEditing(true)}
            className="px-3 py-1.5 rounded-lg font-ui text-xs border border-sepia/20 text-charcoal hover:border-golden/40"
          >
            Edit
          </button>
        ) : (
          <div className="flex gap-2">
            <button type="button" onClick={() => setEditing(false)} className="px-3 py-1.5 rounded-lg font-ui text-xs border border-sepia/20 text-sepia">
              Cancel
            </button>
            <button type="button" onClick={handleSave} disabled={saving} className="px-3 py-1.5 rounded-lg font-ui text-xs bg-golden text-charcoal disabled:opacity-50">
              {saving ? 'Saving...' : 'Save Style'}
            </button>
          </div>
        )}
      </div>
      <div className="space-y-4">
        <div>
          <label className="block font-ui text-xs text-sepia uppercase tracking-wide mb-1">Thematic statement</label>
          {editing ? (
            <textarea value={thematic} onChange={(e) => setThematic(e.target.value)} rows={2} className="w-full px-3 py-2 rounded-lg border border-sepia/20 font-body text-sm" />
          ) : (
            <blockquote className="font-body text-sm text-sepia border-l-2 border-golden/50 pl-3">{thematic || '—'}</blockquote>
          )}
        </div>
        <div>
          <label className="block font-ui text-xs text-sepia uppercase tracking-wide mb-1">Mood keywords</label>
          {editing ? (
            <input type="text" value={moodCsv} onChange={(e) => setMoodCsv(e.target.value)} placeholder="comma-separated" className="w-full px-3 py-2 rounded-lg border border-sepia/20 font-ui text-sm" />
          ) : (
            <div className="flex flex-wrap gap-1">
              {moodCsv ? moodCsv.split(',').map((s, i) => (
                <span key={i} className="px-2 py-0.5 rounded-full bg-sepia/10 text-sepia font-ui text-xs">{s.trim()}</span>
              )) : '—'}
            </div>
          )}
        </div>
        <div>
          <label className="block font-ui text-xs text-sepia uppercase tracking-wide mb-1">Visual style / typography</label>
          {editing ? (
            <input type="text" value={styleTagsCsv} onChange={(e) => setStyleTagsCsv(e.target.value)} placeholder="comma-separated" className="w-full px-3 py-2 rounded-lg border border-sepia/20 font-ui text-sm" />
          ) : (
            <div className="flex flex-wrap gap-1">
              {styleTagsCsv ? styleTagsCsv.split(',').map((s, i) => (
                <span key={i} className="px-2 py-0.5 rounded-full bg-golden/20 text-golden font-ui text-xs">{s.trim()}</span>
              )) : '—'}
            </div>
          )}
        </div>
        <div>
          <label className="block font-ui text-xs text-sepia uppercase tracking-wide mb-1">Color palette</label>
          {editing ? (
            <div className="grid grid-cols-2 gap-2">
              {(['dominant', 'accent', 'temperature', 'contrast', 'saturation'] as const).map((k) => (
                <div key={k}>
                  <span className="font-ui text-[10px] text-sepia capitalize">{k}</span>
                  <input type="text" value={colorPalette[k] ?? ''} onChange={(e) => setColorPalette((p) => ({ ...p, [k]: e.target.value }))} className="w-full px-2 py-1 rounded border border-sepia/20 text-xs" />
                </div>
              ))}
            </div>
          ) : (
            <div className="flex flex-wrap gap-2 items-center">
              {(colorPalette.dominant || colorPalette.accent) && (
                <>
                  {colorPalette.dominant && <span className="inline-block w-6 h-6 rounded-full border border-sepia/30" style={{ backgroundColor: colorPalette.dominant }} title="dominant" />}
                  {colorPalette.accent && <span className="inline-block w-6 h-6 rounded-full border border-sepia/30" style={{ backgroundColor: colorPalette.accent }} title="accent" />}
                </>
              )}
              {[colorPalette.temperature, colorPalette.contrast, colorPalette.saturation].filter(Boolean).join(' · ') || '—'}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

function CharacterCard({
  character,
  isMain,
  onToggle,
  isEditing,
  editDraft,
  onEdit,
  onSave,
  onCancel,
  onDraftChange,
  editError,
}: {
  character: Character;
  isMain: boolean;
  onToggle: () => void;
  isEditing?: boolean;
  editDraft?: Record<string, string> | null;
  onEdit?: () => void;
  onSave?: (data: Record<string, string>) => void;
  onCancel?: () => void;
  onDraftChange?: (key: string, value: string) => void;
  editError?: string | null;
}) {
  const onto = character.ontology;
  const tokens = character.entity_visual_tokens;
  const hasDetails = !!(
    onto?.entity_class || onto?.search_archetype || (onto?.visual_markers?.length) ||
    character.visual_type || (character.typical_emotions) ||
    tokens?.core_tokens?.length || tokens?.style_tokens?.length ||
    tokens?.archetype_tokens?.length || character.search_visual_analog ||
    character.canonical_search_name || character.is_well_known_entity
  );
  const draft = editDraft ?? {};

  if (isEditing && onSave && onCancel) {
    return (
      <div className="p-4 rounded-xl border-2 border-golden/50 bg-white shadow-sm">
        <div className="flex items-start gap-3" onClick={(e) => e.stopPropagation()}>
          <Star size={20} className="mt-0.5 flex-shrink-0 text-sepia/30" aria-hidden />
          <div className="flex-1 space-y-2 min-w-0">
            <label className="block font-ui text-xs text-sepia">Name</label>
            <input value={draft.name ?? ''} onChange={(e) => onDraftChange?.('name', e.target.value)} className="w-full px-2 py-1 rounded border border-sepia/20 text-sm" />
            <label className="block font-ui text-xs text-sepia">Description</label>
            <textarea value={draft.physical_description ?? ''} onChange={(e) => onDraftChange?.('physical_description', e.target.value)} rows={2} className="w-full px-2 py-1 rounded border border-sepia/20 text-xs" />
            <label className="block font-ui text-xs text-sepia">Full description (search)</label>
            <textarea value={draft.full_description ?? ''} onChange={(e) => onDraftChange?.('full_description', e.target.value)} rows={2} className="w-full px-2 py-1 rounded border border-sepia/20 text-xs" />
            <label className="block font-ui text-xs text-sepia">Personality traits (comma-separated)</label>
            <input value={draft.personality_traits ?? ''} onChange={(e) => onDraftChange?.('personality_traits', e.target.value)} className="w-full px-2 py-1 rounded border border-sepia/20 text-sm" />
            {editError && <p className="font-ui text-xs text-red-600">{editError}</p>}
            <div className="flex gap-2 pt-2">
              <button type="button" onClick={onCancel} className="px-3 py-1.5 rounded font-ui text-xs border border-sepia/20">Cancel</button>
              <button type="button" onClick={() => onSave(draft)} className="px-3 py-1.5 rounded font-ui text-xs bg-golden text-charcoal">Save</button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      onClick={onToggle}
      className={`p-4 rounded-xl border-2 cursor-pointer transition-all ${
        isMain ? 'border-golden bg-golden/10 shadow-sm' : 'border-sepia/15 bg-white/50 hover:border-golden/40'
      }`}
    >
      <div className="flex items-start gap-3">
        <Star
          size={20}
          className={`mt-0.5 flex-shrink-0 transition-colors ${isMain ? 'text-golden fill-golden' : 'text-sepia/30'}`}
        />
        <div className="flex-1 space-y-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            <span className="block font-ui text-sm font-semibold text-charcoal">{character.name}</span>
            {onEdit && (
              <button type="button" onClick={(e) => { e.stopPropagation(); onEdit(); }} className="p-1 rounded text-sepia hover:bg-golden/20 hover:text-golden" title="Edit"><Pencil size={14} /></button>
            )}
          </div>
          {character.physical_description && (
            <p className="font-body text-xs text-sepia leading-relaxed">{character.physical_description}</p>
          )}
          {character.personality_traits && (
            <p className="font-ui text-xs text-sepia/70">Traits: {character.personality_traits}</p>
          )}
          {hasDetails && (
            <EntitySection title="Онтология и визуальные данные" defaultOpen={false}>
              {(onto?.entity_class || onto?.search_archetype) && (
                <div className="flex flex-wrap gap-1">
                  {onto.entity_class && (
                    <span className="px-2 py-0.5 rounded-full bg-sepia/10 text-sepia font-ui text-xs">
                      Class: {onto.entity_class}
                    </span>
                  )}
                  {onto.search_archetype && (
                    <span className="px-2 py-0.5 rounded-full bg-golden/20 text-golden font-ui text-xs flex items-center gap-1">
                      <Sparkles size={12} /> {onto.search_archetype}
                    </span>
                  )}
                </div>
              )}
              {character.visual_type && (
                <p className="font-ui text-xs text-sepia">Тип: {character.visual_type}</p>
              )}
              {onto?.visual_markers?.length ? (
                <div className="flex flex-wrap gap-1">
                  {onto.visual_markers.slice(0, 6).map((m, i) => (
                    <span key={i} className="px-2 py-0.5 rounded bg-sepia/10 text-sepia font-ui text-xs">
                      {m}
                    </span>
                  ))}
                </div>
              ) : null}
              {character.typical_emotions && (
                <p className="font-ui text-xs text-sepia/80">Эмоции: {character.typical_emotions}</p>
              )}
              {(tokens?.core_tokens?.length || tokens?.style_tokens?.length || tokens?.archetype_tokens?.length) ? (
                <div className="space-y-1">
                  {tokens.core_tokens?.length ? (
                    <div className="flex flex-wrap gap-1">
                      <Tag size={12} className="text-sepia/60 mt-0.5" />
                      {tokens.core_tokens.slice(0, 5).map((t, i) => (
                        <span key={i} className="px-1.5 py-0.5 rounded bg-charcoal/5 text-charcoal/80 font-ui text-xs">{t}</span>
                      ))}
                    </div>
                  ) : null}
                  {tokens.style_tokens?.length ? (
                    <p className="font-ui text-xs text-sepia/80">Стиль: {tokens.style_tokens.join(', ')}</p>
                  ) : null}
                  {tokens.archetype_tokens?.length ? (
                    <p className="font-ui text-xs text-sepia/80">Архетип: {tokens.archetype_tokens.join(', ')}</p>
                  ) : null}
                </div>
              ) : null}
              {character.search_visual_analog && (
                <p className="font-ui text-xs text-sepia/80 italic">Аналог для поиска: {character.search_visual_analog}</p>
              )}
              {(character.is_well_known_entity && character.canonical_search_name) && (
                <p className="font-ui text-xs text-sepia/80">Известная сущность: {character.canonical_search_name}</p>
              )}
            </EntitySection>
          )}
        </div>
      </div>
    </div>
  );
}

function LocationCard({
  location,
  isMain,
  onToggle,
  isEditing,
  editDraft,
  onEdit,
  onSave,
  onCancel,
  onDraftChange,
  editError,
}: {
  location: Location;
  isMain: boolean;
  onToggle: () => void;
  isEditing?: boolean;
  editDraft?: Record<string, string> | null;
  onEdit?: () => void;
  onSave?: (data: Record<string, string>) => void;
  onCancel?: () => void;
  onDraftChange?: (key: string, value: string) => void;
  editError?: string | null;
}) {
  const onto = location.ontology;
  const tokens = location.entity_visual_tokens;
  const hasDetails = !!(
    onto?.entity_class || onto?.search_archetype || (onto?.visual_markers?.length) ||
    tokens?.core_tokens?.length || tokens?.style_tokens?.length ||
    location.search_visual_analog || location.canonical_search_name || location.is_well_known_entity
  );
  const draft = editDraft ?? {};

  if (isEditing && onSave && onCancel) {
    return (
      <div className="p-4 rounded-xl border-2 border-golden/50 bg-white shadow-sm">
        <div className="flex items-start gap-3" onClick={(e) => e.stopPropagation()}>
          <Star size={20} className="mt-0.5 flex-shrink-0 text-sepia/30" aria-hidden />
          <div className="flex-1 space-y-2 min-w-0">
            <label className="block font-ui text-xs text-sepia">Name</label>
            <input value={draft.name ?? ''} onChange={(e) => onDraftChange?.('name', e.target.value)} className="w-full px-2 py-1 rounded border border-sepia/20 text-sm" />
            <label className="block font-ui text-xs text-sepia">Visual description</label>
            <textarea value={draft.visual_description ?? ''} onChange={(e) => onDraftChange?.('visual_description', e.target.value)} rows={2} className="w-full px-2 py-1 rounded border border-sepia/20 text-xs" />
            <label className="block font-ui text-xs text-sepia">Full description (search)</label>
            <textarea value={draft.full_description ?? ''} onChange={(e) => onDraftChange?.('full_description', e.target.value)} rows={2} className="w-full px-2 py-1 rounded border border-sepia/20 text-xs" />
            <label className="block font-ui text-xs text-sepia">Atmosphere</label>
            <input value={draft.atmosphere ?? ''} onChange={(e) => onDraftChange?.('atmosphere', e.target.value)} className="w-full px-2 py-1 rounded border border-sepia/20 text-sm" />
            {editError && <p className="font-ui text-xs text-red-600">{editError}</p>}
            <div className="flex gap-2 pt-2">
              <button type="button" onClick={onCancel} className="px-3 py-1.5 rounded font-ui text-xs border border-sepia/20">Cancel</button>
              <button type="button" onClick={() => onSave(draft)} className="px-3 py-1.5 rounded font-ui text-xs bg-golden text-charcoal">Save</button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      onClick={onToggle}
      className={`p-4 rounded-xl border-2 cursor-pointer transition-all ${
        isMain ? 'border-golden bg-golden/10 shadow-sm' : 'border-sepia/15 bg-white/50 hover:border-golden/40'
      }`}
    >
      <div className="flex items-start gap-3">
        <Star
          size={20}
          className={`mt-0.5 flex-shrink-0 transition-colors ${isMain ? 'text-golden fill-golden' : 'text-sepia/30'}`}
        />
        <div className="flex-1 space-y-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            <span className="block font-ui text-sm font-semibold text-charcoal">{location.name}</span>
            {onEdit && (
              <button type="button" onClick={(e) => { e.stopPropagation(); onEdit(); }} className="p-1 rounded text-sepia hover:bg-golden/20 hover:text-golden" title="Edit"><Pencil size={14} /></button>
            )}
          </div>
          {location.visual_description && (
            <p className="font-body text-xs text-sepia leading-relaxed">{location.visual_description}</p>
          )}
          {location.atmosphere && (
            <p className="font-ui text-xs text-sepia/70">Atmosphere: {location.atmosphere}</p>
          )}
          {hasDetails && (
            <EntitySection title="Онтология и визуальные данные" defaultOpen={false}>
              {(onto?.entity_class || onto?.search_archetype) && (
                <div className="flex flex-wrap gap-1">
                  {onto.entity_class && (
                    <span className="px-2 py-0.5 rounded-full bg-sepia/10 text-sepia font-ui text-xs">Class: {onto.entity_class}</span>
                  )}
                  {onto.search_archetype && (
                    <span className="px-2 py-0.5 rounded-full bg-golden/20 text-golden font-ui text-xs flex items-center gap-1">
                      <Sparkles size={12} /> {onto.search_archetype}
                    </span>
                  )}
                </div>
              )}
              {onto?.visual_markers?.length ? (
                <div className="flex flex-wrap gap-1">
                  {onto.visual_markers.slice(0, 6).map((m, i) => (
                    <span key={i} className="px-2 py-0.5 rounded bg-sepia/10 text-sepia font-ui text-xs">{m}</span>
                  ))}
                </div>
              ) : null}
              {(tokens?.core_tokens?.length || tokens?.style_tokens?.length) ? (
                <div className="space-y-1">
                  {tokens.core_tokens?.length ? (
                    <div className="flex flex-wrap gap-1">
                      <Tag size={12} className="text-sepia/60 mt-0.5" />
                      {tokens.core_tokens.slice(0, 5).map((t, i) => (
                        <span key={i} className="px-1.5 py-0.5 rounded bg-charcoal/5 text-charcoal/80 font-ui text-xs">{t}</span>
                      ))}
                    </div>
                  ) : null}
                  {tokens.style_tokens?.length ? (
                    <p className="font-ui text-xs text-sepia/80">Стиль: {tokens.style_tokens.join(', ')}</p>
                  ) : null}
                </div>
              ) : null}
              {location.search_visual_analog && (
                <p className="font-ui text-xs text-sepia/80 italic">Аналог для поиска: {location.search_visual_analog}</p>
              )}
              {(location.is_well_known_entity && location.canonical_search_name) && (
                <p className="font-ui text-xs text-sepia/80">Известная сущность: {location.canonical_search_name}</p>
              )}
            </EntitySection>
          )}
        </div>
      </div>
    </div>
  );
}

function ArtefactCard({
  artefact,
  isMain,
  onToggle,
  isEditing,
  editDraft,
  onEdit,
  onSave,
  onCancel,
  onDraftChange,
  editError,
}: {
  artefact: Artefact;
  isMain: boolean;
  onToggle: () => void;
  isEditing?: boolean;
  editDraft?: Record<string, string> | null;
  onEdit?: () => void;
  onSave?: (data: Record<string, string>) => void;
  onCancel?: () => void;
  onDraftChange?: (key: string, value: string) => void;
  editError?: string | null;
}) {
  const draft = editDraft ?? {};

  if (isEditing && onSave && onCancel) {
    return (
      <div className="p-4 rounded-xl border-2 border-golden/50 bg-white shadow-sm" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-start gap-3">
          <Star size={20} className="mt-0.5 flex-shrink-0 text-sepia/30" aria-hidden />
          <div className="flex-1 space-y-2 min-w-0">
            <label className="block font-ui text-xs text-sepia">Name</label>
            <input value={draft.name ?? ''} onChange={(e) => onDraftChange?.('name', e.target.value)} className="w-full px-2 py-1 rounded border border-sepia/20 text-sm" />
            <label className="block font-ui text-xs text-sepia">Description</label>
            <textarea value={draft.physical_description ?? ''} onChange={(e) => onDraftChange?.('physical_description', e.target.value)} rows={2} className="w-full px-2 py-1 rounded border border-sepia/20 text-xs" />
            <label className="block font-ui text-xs text-sepia">Full description (search)</label>
            <textarea value={draft.full_description ?? ''} onChange={(e) => onDraftChange?.('full_description', e.target.value)} rows={2} className="w-full px-2 py-1 rounded border border-sepia/20 text-xs" />
            <label className="block font-ui text-xs text-sepia">Symbolic role</label>
            <input value={draft.symbolic_role ?? ''} onChange={(e) => onDraftChange?.('symbolic_role', e.target.value)} className="w-full px-2 py-1 rounded border border-sepia/20 text-sm" />
            {editError && <p className="font-ui text-xs text-red-600">{editError}</p>}
            <div className="flex gap-2 pt-2">
              <button type="button" onClick={onCancel} className="px-3 py-1.5 rounded font-ui text-xs border border-sepia/20">Cancel</button>
              <button type="button" onClick={() => onSave(draft)} className="px-3 py-1.5 rounded font-ui text-xs bg-golden text-charcoal">Save</button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      onClick={onToggle}
      className={`p-4 rounded-xl border-2 cursor-pointer transition-all ${
        isMain ? 'border-golden bg-golden/10 shadow-sm' : 'border-sepia/15 bg-white/50 hover:border-golden/40'
      }`}
    >
      <div className="flex items-start gap-3">
        <Star size={20} className={`mt-0.5 flex-shrink-0 ${isMain ? 'text-golden fill-golden' : 'text-sepia/30'}`} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            <span className="block font-ui text-sm font-semibold text-charcoal">{artefact.name}</span>
            {onEdit && (
              <button type="button" onClick={(e) => { e.stopPropagation(); onEdit(); }} className="p-1 rounded text-sepia hover:bg-golden/20 hover:text-golden" title="Edit"><Pencil size={14} /></button>
            )}
          </div>
          {artefact.physical_description && (
            <p className="font-body text-xs text-sepia mt-1 leading-relaxed">{artefact.physical_description}</p>
          )}
        </div>
      </div>
    </div>
  );
}

function SceneCard({
  scene,
  onToggleSelected,
  onSave,
}: {
  scene: SceneResponse;
  onToggleSelected: () => void;
  onSave: (updates: { title?: string; narrative_summary?: string; dramatic_score_avg?: number }) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [title, setTitle] = useState(scene.title ?? '');
  const [narrative, setNarrative] = useState(scene.narrative_summary ?? '');
  const [dramaticScore, setDramaticScore] = useState<string>(scene.dramatic_score_avg != null ? String(scene.dramatic_score_avg) : '');

  useEffect(() => {
    setTitle(scene.title ?? '');
    setNarrative(scene.narrative_summary ?? '');
    setDramaticScore(scene.dramatic_score_avg != null ? String(scene.dramatic_score_avg) : '');
  }, [scene.id, scene.title, scene.narrative_summary, scene.dramatic_score_avg]);

  const handleSave = () => {
    const num = dramaticScore === '' ? undefined : parseFloat(dramaticScore);
    onSave({ title: title || undefined, narrative_summary: narrative || undefined, dramatic_score_avg: num });
    setEditing(false);
  };

  return (
    <div
      className={`p-4 rounded-xl border-2 transition-all space-y-3 ${
        scene.is_selected
          ? 'border-golden bg-golden/5 shadow-sm'
          : 'border-sepia/15 bg-white/50'
      }`}
    >
      <div className="flex items-start gap-3">
        <button
          type="button"
          onClick={onToggleSelected}
          className={`mt-0.5 flex-shrink-0 w-5 h-5 rounded border-2 transition-colors flex items-center justify-center cursor-pointer ${
            scene.is_selected
              ? 'bg-golden border-golden text-white'
              : 'border-sepia/30 hover:border-golden/60'
          }`}
          aria-label={scene.is_selected ? 'Deselect scene' : 'Select scene'}
        >
          {scene.is_selected && (
            <svg width="10" height="8" viewBox="0 0 10 8" fill="none">
              <path d="M1 4L3.5 6.5L9 1" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          )}
        </button>
        <div className="flex-1 space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            {!editing ? (
              (scene.title_display ?? scene.title) && (
                <span className="font-ui text-sm font-semibold text-charcoal">
                  {scene.title_display ?? scene.title}
                </span>
              )
            ) : (
              <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Title" className="px-2 py-1 rounded border border-sepia/20 font-ui text-sm flex-1 min-w-[120px]" />
            )}
            {scene.scene_type && (
              <span className="px-2 py-0.5 rounded-full bg-sepia/10 text-sepia font-ui text-xs">
                {scene.scene_type}
              </span>
            )}
            {scene.illustration_priority && (
              <span className={`px-2 py-0.5 rounded-full font-ui text-xs ${
                scene.illustration_priority === 'high'
                  ? 'bg-golden/20 text-golden'
                  : scene.illustration_priority === 'medium'
                    ? 'bg-sepia/10 text-sepia'
                    : 'bg-gray-100 text-gray-500'
              }`}>
                {scene.illustration_priority} priority
              </span>
            )}
            {onSave && (
              !editing ? (
                <button type="button" onClick={(e) => { e.stopPropagation(); setEditing(true); }} className="p-1 rounded text-sepia hover:bg-golden/20 hover:text-golden" title="Edit"><Pencil size={14} /></button>
              ) : (
                <div className="flex gap-1" onClick={(e) => e.stopPropagation()}>
                  <button type="button" onClick={handleSave} className="px-2 py-1 rounded font-ui text-xs bg-golden text-charcoal">Save</button>
                  <button type="button" onClick={() => setEditing(false)} className="px-2 py-1 rounded font-ui text-xs border border-sepia/20">Cancel</button>
                </div>
              )
            )}
          </div>
          {!editing ? (
            (scene.narrative_summary_display ?? scene.narrative_summary) && (
              <p className="font-body text-xs text-sepia leading-relaxed">
                {scene.narrative_summary_display ?? scene.narrative_summary}
              </p>
            )
          ) : (
            <>
              <label className="block font-ui text-[10px] text-sepia uppercase">Narrative summary</label>
              <textarea value={narrative} onChange={(e) => setNarrative(e.target.value)} rows={3} className="w-full px-2 py-1 rounded border border-sepia/20 text-xs" />
              <label className="block font-ui text-[10px] text-sepia uppercase">Dramatic score (0–1)</label>
              <input type="text" value={dramaticScore} onChange={(e) => setDramaticScore(e.target.value)} className="w-20 px-2 py-1 rounded border border-sepia/20 text-xs" />
            </>
          )}
          {(scene.characters_present?.length > 0 || scene.primary_location) && (
            <div className="flex flex-wrap gap-1">
              {scene.characters_present?.map((name) => (
                <span key={name} className="px-2 py-0.5 rounded-full bg-blue-50 text-blue-600 font-ui text-xs">
                  {name}
                </span>
              ))}
              {scene.primary_location && (
                <span className="px-2 py-0.5 rounded-full bg-green-50 text-green-600 font-ui text-xs">
                  {scene.primary_location}
                </span>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
