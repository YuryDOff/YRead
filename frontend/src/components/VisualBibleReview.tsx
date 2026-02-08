import { useState } from 'react';
import { Check, User, MapPin, Palette, Loader2 } from 'lucide-react';
import type { Character, Location, VisualBible, ReferenceImages } from '../services/api';

type Tab = 'characters' | 'locations' | 'style';

interface Props {
  characters: Character[];
  locations: Location[];
  visualBible: VisualBible;
  referenceImages: ReferenceImages | null;
  onApprove: (
    charSelections: Record<number, string>,
    locSelections: Record<number, string>,
  ) => void;
  loading?: boolean;
}

export default function VisualBibleReview({
  characters,
  locations,
  visualBible,
  referenceImages,
  onApprove,
  loading,
}: Props) {
  const [tab, setTab] = useState<Tab>('characters');
  const [charSel, setCharSel] = useState<Record<number, string>>(() => {
    const init: Record<number, string> = {};
    characters.forEach((c) => {
      if (c.reference_image_url) init[c.id] = c.reference_image_url;
    });
    return init;
  });
  const [locSel, setLocSel] = useState<Record<number, string>>(() => {
    const init: Record<number, string> = {};
    locations.forEach((l) => {
      if (l.reference_image_url) init[l.id] = l.reference_image_url;
    });
    return init;
  });

  const charReady = characters.filter((c) => charSel[c.id]).length;
  const locReady = locations.filter((l) => locSel[l.id]).length;
  const allReady = charReady === characters.length && locReady === locations.length;

  const TABS: { id: Tab; label: string; icon: typeof User }[] = [
    { id: 'characters', label: `Characters (${charReady}/${characters.length})`, icon: User },
    { id: 'locations', label: `Locations (${locReady}/${locations.length})`, icon: MapPin },
    { id: 'style', label: 'Style Summary', icon: Palette },
  ];

  return (
    <div className="w-full max-w-4xl space-y-6">
      <div className="text-center space-y-1">
        <h2 className="font-display text-3xl font-semibold text-charcoal">Visual Bible</h2>
        <p className="text-sepia font-body text-sm">
          Review and select reference images for your characters and locations
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
                  selectedUrl={charSel[char.id] ?? null}
                  onSelect={(url) =>
                    setCharSel((p) => ({ ...p, [char.id]: url }))
                  }
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
                  selectedUrl={locSel[loc.id] ?? null}
                  onSelect={(url) =>
                    setLocSel((p) => ({ ...p, [loc.id]: url }))
                  }
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
  selectedUrl,
  onSelect,
}: {
  name: string;
  description: string;
  extra: string;
  images: { url: string; thumbnail?: string }[];
  selectedUrl: string | null;
  onSelect: (url: string) => void;
}) {
  return (
    <div className="p-4 rounded-xl bg-white/50 border border-sepia/15 space-y-3">
      <div>
        <h4 className="font-display text-lg font-semibold text-charcoal">{name}</h4>
        <p className="font-body text-sm text-sepia leading-relaxed">{description}</p>
        {extra && (
          <p className="font-ui text-xs text-sepia/70 mt-1 italic">{extra}</p>
        )}
      </div>

      {images.length > 0 ? (
        <div className="flex gap-3 overflow-x-auto pb-1">
          {images.map((img, i) => {
            const isSelected = selectedUrl === img.url;
            return (
              <button
                key={i}
                onClick={() => onSelect(img.url)}
                className={`relative shrink-0 w-28 h-28 rounded-lg overflow-hidden
                  border-3 transition-all cursor-pointer
                  ${isSelected
                    ? 'border-golden shadow-md ring-2 ring-golden/30'
                    : 'border-sepia/20 hover:border-golden/50'}`}
              >
                <img
                  src={img.thumbnail || img.url}
                  alt={name}
                  className="w-full h-full object-cover"
                  loading="lazy"
                />
                {isSelected && (
                  <div className="absolute inset-0 bg-golden/20 flex items-center justify-center">
                    <Check size={24} className="text-white drop-shadow" />
                  </div>
                )}
              </button>
            );
          })}
        </div>
      ) : (
        <p className="text-xs font-ui text-sepia/60 italic">
          No reference images available — text description will be used
        </p>
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
