import { useState } from 'react';
import { Check, User, MapPin, Palette, Loader2, Upload, ThumbsUp, ThumbsDown } from 'lucide-react';
import { rateEngine } from '../services/api';
import type { Character, Location, VisualBible, ReferenceImages, ReferenceImageItem, EngineRatingResponse } from '../services/api';

type Tab = 'characters' | 'locations' | 'style';

interface Props {
  characters: Character[];
  locations: Location[];
  visualBible: VisualBible;
  referenceImages: ReferenceImages | null;
  engineRatings?: EngineRatingResponse[];
  onApprove: (
    charSelections: Record<number, string[]>,
    locSelections: Record<number, string[]>,
  ) => void;
  loading?: boolean;
  pageTitle?: string;
  pageDescription?: string;
  bookId?: number;
  onUploadImage?: (entityType: 'character' | 'location', entityId: number) => void;
  onRefsUpdated?: () => void;
  onRatingUpdate?: () => void;
  initialTab?: Tab;
}

export default function VisualBibleReview({
  characters,
  locations,
  visualBible,
  referenceImages,
  engineRatings = [],
  onApprove,
  loading,
  pageTitle = 'Visual Bible',
  pageDescription = 'Review and select reference images for your characters and locations',
  bookId,
  onUploadImage,
  onRefsUpdated,
  onRatingUpdate,
  initialTab,
}: Props) {
  const [tab, setTab] = useState<Tab>(initialTab ?? 'characters');
  const [charSel, setCharSel] = useState<Record<number, string[]>>(() => {
    const init: Record<number, string[]> = {};
    characters.forEach((c) => {
      const urls = c.selected_reference_urls?.length
        ? [...c.selected_reference_urls]
        : (c.reference_image_url ? [c.reference_image_url] : []);
      if (urls.length) init[c.id] = urls;
    });
    return init;
  });
  const [locSel, setLocSel] = useState<Record<number, string[]>>(() => {
    const init: Record<number, string[]> = {};
    locations.forEach((l) => {
      const urls = l.selected_reference_urls?.length
        ? [...l.selected_reference_urls]
        : (l.reference_image_url ? [l.reference_image_url] : []);
      if (urls.length) init[l.id] = urls;
    });
    return init;
  });

  const charReady = characters.filter((c) => (charSel[c.id]?.length ?? 0) > 0).length;
  const locReady = locations.filter((l) => (locSel[l.id]?.length ?? 0) > 0).length;
  const allReady = charReady === characters.length && locReady === locations.length;

  const TABS: { id: Tab; label: string; icon: typeof User }[] = [
    { id: 'characters', label: `Characters (${charReady}/${characters.length})`, icon: User },
    { id: 'locations', label: `Locations (${locReady}/${locations.length})`, icon: MapPin },
    { id: 'style', label: 'Style Summary', icon: Palette },
  ];

  return (
    <div className="w-full max-w-4xl space-y-6">
      <div className="text-center space-y-1">
        <h2 className="font-display text-3xl font-semibold text-charcoal">{pageTitle}</h2>
        <p className="text-sepia font-body text-sm">
          {pageDescription}
        </p>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-sepia/20 gap-1">
        {TABS.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setTab(id)}
            className={`flex items-center gap-2 px-4 py-2.5 font-ui text-sm transition-colors
              cursor-pointer border-b-2 -mb-px
              ${tab === id
                ? 'border-golden text-charcoal font-semibold'
                : 'border-transparent text-sepia hover:text-charcoal'}`}
          >
            <Icon size={16} />
            {label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="min-h-[300px]">
        {tab === 'characters' && (
          <div className="space-y-6">
            {characters.map((char) => {
              const images =
                referenceImages?.characters?.[char.name] ?? [];
              return (
                <EntityCard
                  key={char.id}
                  name={char.name}
                  description={char.physical_description ?? ''}
                  extra={char.personality_traits ?? ''}
                  images={images}
                  selectedUrls={charSel[char.id] ?? []}
                  onToggleSelect={(url) => {
                    setCharSel((p) => {
                      const prev = p[char.id] ?? [];
                      const next = prev.includes(url)
                        ? prev.filter((u) => u !== url)
                        : [...prev, url];
                      return { ...p, [char.id]: next };
                    });
                  }}
                  onUploadImage={bookId && onUploadImage ? () => onUploadImage('character', char.id) : undefined}
                  bookId={bookId}
                  engineRatings={engineRatings}
                  onRatingUpdate={onRatingUpdate}
                />
              );
            })}
            {characters.length === 0 && (
              <p className="text-sepia font-ui text-sm text-center py-8">
                No characters extracted yet.
              </p>
            )}
          </div>
        )}

        {tab === 'locations' && (
          <div className="space-y-6">
            {locations.map((loc) => {
              const images =
                referenceImages?.locations?.[loc.name] ?? [];
              return (
                <EntityCard
                  key={loc.id}
                  name={loc.name}
                  description={loc.visual_description ?? ''}
                  extra={loc.atmosphere ?? ''}
                  images={images}
                  selectedUrls={locSel[loc.id] ?? []}
                  onToggleSelect={(url) => {
                    setLocSel((p) => {
                      const prev = p[loc.id] ?? [];
                      const next = prev.includes(url)
                        ? prev.filter((u) => u !== url)
                        : [...prev, url];
                      return { ...p, [loc.id]: next };
                    });
                  }}
                  onUploadImage={bookId && onUploadImage ? () => onUploadImage('location', loc.id) : undefined}
                  bookId={bookId}
                  engineRatings={engineRatings}
                  onRatingUpdate={onRatingUpdate}
                />
              );
            })}
            {locations.length === 0 && (
              <p className="text-sepia font-ui text-sm text-center py-8">
                No locations extracted yet.
              </p>
            )}
          </div>
        )}

        {tab === 'style' && (
          <div className="space-y-4 p-4 rounded-xl bg-white/50 border border-sepia/15">
            <Row label="Style" value={visualBible.style_category} />
            <Row label="Tone" value={visualBible.tone_description} />
            <Row label="Frequency" value={`Every ${visualBible.illustration_frequency} pages`} />
            <Row label="Layout" value={visualBible.layout_style === 'inline_classic' ? 'Inline Classic' : 'Anime Panels'} />
          </div>
        )}
      </div>

      {/* Approve button */}
      <button
        onClick={() => onApprove(charSel, locSel)}
        disabled={!allReady || loading}
        type="button"
        className="w-full flex items-center justify-center gap-2 px-6 py-3 rounded-lg
                   font-ui font-semibold text-paper-cream bg-sage hover:bg-sage/90
                   disabled:opacity-40 disabled:cursor-not-allowed
                   transition-colors shadow cursor-pointer"
      >
        {loading ? (
          <Loader2 size={18} className="animate-spin" />
        ) : (
          <Check size={18} />
        )}
        {loading ? 'Saving...' : 'Approve & Continue'}
      </button>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Sub-components                                                      */
/* ------------------------------------------------------------------ */

function EntityCard({
  name,
  description,
  extra,
  images,
  selectedUrls,
  onToggleSelect,
  onUploadImage,
  bookId,
  engineRatings = [],
  onRatingUpdate,
}: {
  name: string;
  description: string;
  extra: string;
  images: ReferenceImageItem[];
  selectedUrls: string[];
  onToggleSelect: (url: string) => void;
  onUploadImage?: () => void;
  bookId?: number;
  engineRatings?: EngineRatingResponse[];
  onRatingUpdate?: () => void;
}) {
  const [expandedImage, setExpandedImage] = useState<ReferenceImageItem | null>(null);
  const [lightboxDisplayUrl, setLightboxDisplayUrl] = useState('');
  const sourceLabel = (src?: string) => (src === 'unsplash' ? 'Unsplash' : src === 'serpapi' ? 'SerpAPI' : src === 'user' ? 'User' : src ?? null);
  const ratingByProvider = (provider: string) => engineRatings.find((r) => r.provider === provider);

  function handleRate(source: string | undefined, action: 'like' | 'dislike') {
    if (!bookId || !source || source === 'user') return;
    rateEngine(bookId, { provider: source, action }).then(() => onRatingUpdate?.()).catch(console.error);
  }

  return (
    <div className="p-4 rounded-xl bg-white/50 border border-sepia/15 space-y-3">
      <div className="flex items-start justify-between gap-2">
        <div>
          <h4 className="font-display text-lg font-semibold text-charcoal">{name}</h4>
        <p className="font-body text-sm text-sepia leading-relaxed">{description}</p>
        {extra && (
          <p className="font-ui text-xs text-sepia/70 mt-1 italic">{extra}</p>
        )}
        </div>
        {onUploadImage && (
          <button type="button" onClick={onUploadImage} className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-ui text-xs text-charcoal border border-sepia/25 hover:border-golden/50 hover:bg-white transition-colors cursor-pointer shrink-0">
            <Upload size={14} />
            Add image
          </button>
        )}
      </div>

      {images.length > 0 ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
          {images.map((img, i) => {
            const isSelected = selectedUrls.includes(img.url);
            return (
              <div key={i} className="flex flex-col gap-1">
                <button
                  type="button"
                  onClick={() => { setExpandedImage(img); setLightboxDisplayUrl(img.url); }}
                  className={`relative aspect-square w-full rounded-lg overflow-hidden border-3 transition-all cursor-pointer ${isSelected ? 'border-golden shadow-md ring-2 ring-golden/30' : 'border-sepia/20 hover:border-golden/50'}`}
                >
                  <img src={img.thumbnail || img.url} alt={name} className="w-full h-full object-cover" loading="lazy" />
                  {img.source && (
                    <span className="absolute bottom-0 left-0 right-0 py-0.5 px-1.5 bg-charcoal/70 text-white font-ui text-[10px] truncate text-center">
                      {sourceLabel(img.source)}
                    </span>
                  )}
                  {isSelected && (
                    <div className="absolute inset-0 bg-golden/20 flex items-center justify-center pointer-events-none">
                      <Check size={24} className="text-white drop-shadow" />
                    </div>
                  )}
                </button>
                {bookId && img.source && img.source !== 'user' && (() => {
                  const rating = ratingByProvider(img.source);
                  const likes = rating?.likes ?? 0;
                  const dislikes = rating?.dislikes ?? 0;
                  return (
                    <div className="flex gap-1 justify-center items-center">
                      <button
                        type="button"
                        title="Good source (+1)"
                        onClick={(e) => { e.stopPropagation(); handleRate(img.source, 'like'); }}
                        className="flex-1 flex items-center justify-center gap-0.5 py-0.5 rounded text-xs
                                   text-green-600 hover:bg-green-50 transition-colors cursor-pointer"
                      >
                        <ThumbsUp size={11} />
                        {likes > 0 && <span className="text-[10px]">({likes})</span>}
                      </button>
                      <button
                        type="button"
                        title="Poor source (+1)"
                        onClick={(e) => { e.stopPropagation(); handleRate(img.source, 'dislike'); }}
                        className="flex-1 flex items-center justify-center gap-0.5 py-0.5 rounded text-xs
                                   text-red-500 hover:bg-red-50 transition-colors cursor-pointer"
                      >
                        <ThumbsDown size={11} />
                        {dislikes > 0 && <span className="text-[10px]">({dislikes})</span>}
                      </button>
                    </div>
                  );
                })()}
              </div>
            );
          })}
        </div>
      ) : (
        <p className="text-xs font-ui text-sepia/60 italic">
          No reference images available — run a search or add your own image
        </p>
      )}

      {/* Lightbox: full-size image + Select for visual bible */}
      {expandedImage && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-charcoal/70 p-4"
          onClick={() => setExpandedImage(null)}
          role="dialog"
          aria-modal="true"
          aria-label="Reference image preview"
        >
          <div
            className="relative max-w-4xl w-full max-h-[90vh] flex flex-col items-center gap-4 bg-paper-cream rounded-xl shadow-xl p-4"
            onClick={(e) => e.stopPropagation()}
          >
            <img
              src={lightboxDisplayUrl}
              alt={name}
              className="max-w-full max-h-[70vh] w-auto h-auto object-contain rounded-lg"
              onError={() => {
                const fallback = expandedImage.thumbnail || expandedImage.url;
                if (fallback !== lightboxDisplayUrl) setLightboxDisplayUrl(fallback);
              }}
            />
            <div className="flex flex-wrap gap-3 justify-center">
              <button
                type="button"
                onClick={() => { onToggleSelect(expandedImage.url); setExpandedImage(null); }}
                className="flex items-center gap-2 px-4 py-2 rounded-lg font-ui font-semibold text-paper-cream bg-sage hover:bg-sage/90 cursor-pointer transition-colors"
              >
                <Check size={18} />
                Select for visual bible
              </button>
              {bookId && expandedImage.source && expandedImage.source !== 'user' && (() => {
                const rating = ratingByProvider(expandedImage.source);
                const likes = rating?.likes ?? 0;
                const dislikes = rating?.dislikes ?? 0;
                return (
                  <>
                    <span className="font-ui text-xs text-sepia">
                      {sourceLabel(expandedImage.source)} — Likes: {likes}, Dislikes: {dislikes}
                    </span>
                    <button
                      type="button"
                      onClick={() => handleRate(expandedImage.source, 'like')}
                      title="Each click adds a like"
                      className="flex items-center gap-2 px-4 py-2 rounded-lg font-ui text-green-700 bg-green-50 hover:bg-green-100 cursor-pointer transition-colors"
                    >
                      <ThumbsUp size={16} />
                      Good source (+1)
                    </button>
                    <button
                      type="button"
                      onClick={() => handleRate(expandedImage.source, 'dislike')}
                      title="Each click adds a dislike"
                      className="flex items-center gap-2 px-4 py-2 rounded-lg font-ui text-red-600 bg-red-50 hover:bg-red-100 cursor-pointer transition-colors"
                    >
                      <ThumbsDown size={16} />
                      Poor source (+1)
                    </button>
                  </>
                );
              })()}
              <button
                type="button"
                onClick={() => setExpandedImage(null)}
                className="px-4 py-2 rounded-lg font-ui text-charcoal bg-sepia/20 hover:bg-sepia/30 cursor-pointer transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function Row({ label, value }: { label: string; value: string | null | undefined }) {
  return (
    <div className="flex items-baseline gap-3">
      <span className="font-ui text-xs text-sepia uppercase tracking-wide w-24 shrink-0">
        {label}
      </span>
      <span className="font-body text-sm text-charcoal">{value ?? '—'}</span>
    </div>
  );
}
