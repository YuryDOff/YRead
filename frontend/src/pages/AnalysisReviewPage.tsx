import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Users, MapPin, Film, Search, Loader2, ArrowLeft, Star } from 'lucide-react';
import { useBook } from '../context/BookContext';
import {
  getCharacters,
  getLocations,
  getScenes,
  updateEntitySelections,
  updateScene,
  type Character,
  type Location,
  type SceneResponse,
} from '../services/api';

type Tab = 'characters' | 'locations' | 'scenes';

export default function AnalysisReviewPage() {
  const navigate = useNavigate();
  const ctx = useBook();

  const [activeTab, setActiveTab] = useState<Tab>('characters');
  const [characters, setCharacters] = useState<Character[]>([]);
  const [locations, setLocations] = useState<Location[]>([]);
  const [scenes, setScenes] = useState<SceneResponse[]>([]);
  const [charMainFlags, setCharMainFlags] = useState<Record<number, boolean>>({});
  const [locMainFlags, setLocMainFlags] = useState<Record<number, boolean>>({});
  const [loading, setLoading] = useState(true);
  const [searching, setSearching] = useState(false);

  useEffect(() => {
    if (!ctx.book) {
      navigate('/');
      return;
    }

    async function load() {
      try {
        const [chars, locs, scns] = await Promise.all([
          getCharacters(ctx.book!.id),
          getLocations(ctx.book!.id),
          getScenes(ctx.book!.id).catch(() => []),
        ]);
        setCharacters(chars);
        setLocations(locs);
        setScenes(scns);

        const cFlags: Record<number, boolean> = {};
        for (const c of chars) cFlags[c.id] = c.is_main === 1;
        setCharMainFlags(cFlags);

        const lFlags: Record<number, boolean> = {};
        for (const l of locs) lFlags[l.id] = l.is_main === 1;
        setLocMainFlags(lFlags);
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

  const handleUpdateScenePrompt = useCallback(async (sceneId: number, draft: string) => {
    if (!ctx.book) return;
    setScenes((prev) =>
      prev.map((s) => (s.id === sceneId ? { ...s, scene_prompt_draft: draft } : s)),
    );
    try {
      await updateScene(ctx.book.id, sceneId, { scene_prompt_draft: draft });
    } catch (err) {
      console.error('Failed to save scene prompt', err);
    }
  }, [ctx.book]);

  const selectedCharCount = Object.values(charMainFlags).filter(Boolean).length;
  const selectedLocCount = Object.values(locMainFlags).filter(Boolean).length;
  const selectedSceneCount = scenes.filter((s) => s.is_selected).length;

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
    { id: 'scenes', label: 'Scenes', count: selectedSceneCount, icon: Film },
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
              {characters.map((c) => {
                const isMain = !!charMainFlags[c.id];
                return (
                  <div
                    key={c.id}
                    onClick={() => toggleChar(c.id)}
                    className={`p-4 rounded-xl border-2 cursor-pointer transition-all ${
                      isMain
                        ? 'border-golden bg-golden/10 shadow-sm'
                        : 'border-sepia/15 bg-white/50 hover:border-golden/40'
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <Star
                        size={20}
                        className={`mt-0.5 flex-shrink-0 transition-colors ${
                          isMain ? 'text-golden fill-golden' : 'text-sepia/30'
                        }`}
                      />
                      <div className="flex-1 space-y-1">
                        <span className="block font-ui text-sm font-semibold text-charcoal">
                          {c.name}
                        </span>
                        {c.physical_description && (
                          <p className="font-body text-xs text-sepia leading-relaxed">
                            {c.physical_description}
                          </p>
                        )}
                        {c.personality_traits && (
                          <p className="font-ui text-xs text-sepia/70">
                            Traits: {c.personality_traits}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
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
              {locations.map((l) => {
                const isMain = !!locMainFlags[l.id];
                return (
                  <div
                    key={l.id}
                    onClick={() => toggleLoc(l.id)}
                    className={`p-4 rounded-xl border-2 cursor-pointer transition-all ${
                      isMain
                        ? 'border-golden bg-golden/10 shadow-sm'
                        : 'border-sepia/15 bg-white/50 hover:border-golden/40'
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <Star
                        size={20}
                        className={`mt-0.5 flex-shrink-0 transition-colors ${
                          isMain ? 'text-golden fill-golden' : 'text-sepia/30'
                        }`}
                      />
                      <div className="flex-1 space-y-1">
                        <span className="block font-ui text-sm font-semibold text-charcoal">
                          {l.name}
                        </span>
                        {l.visual_description && (
                          <p className="font-body text-xs text-sepia leading-relaxed">
                            {l.visual_description}
                          </p>
                        )}
                        {l.atmosphere && (
                          <p className="font-ui text-xs text-sepia/70">
                            Atmosphere: {l.atmosphere}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
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
                    onEditPrompt={(draft) => handleUpdateScenePrompt(scene.id, draft)}
                  />
                ))}
              </div>
            )}
          </section>
        )}

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
            disabled={searching || (selectedCharCount === 0 && selectedLocCount === 0)}
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
                Prepare reference search ({selectedCharCount + selectedLocCount} entities)
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

function SceneCard({
  scene,
  onToggleSelected,
  onEditPrompt,
}: {
  scene: SceneResponse;
  onToggleSelected: () => void;
  onEditPrompt: (draft: string) => void;
}) {
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
            {(scene.title_display ?? scene.title) && (
              <span className="font-ui text-sm font-semibold text-charcoal">
                {scene.title_display ?? scene.title}
              </span>
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
          </div>
          {(scene.narrative_summary_display ?? scene.narrative_summary) && (
            <p className="font-body text-xs text-sepia leading-relaxed">
              {scene.narrative_summary_display ?? scene.narrative_summary}
            </p>
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
          <div>
            <label className="block font-ui text-xs text-sepia uppercase tracking-wide mb-1">
              Scene prompt draft
            </label>
            <textarea
              value={scene.scene_prompt_draft ?? ''}
              onChange={(e) => onEditPrompt(e.target.value)}
              rows={2}
              onClick={(e) => e.stopPropagation()}
              className="w-full px-3 py-2 rounded-lg border border-sepia/20 font-body text-xs
                         text-charcoal placeholder-sepia/50 focus:border-golden focus:outline-none
                         resize-none"
              placeholder="AI-generated scene prompt…"
            />
          </div>
        </div>
      </div>
    </div>
  );
}
