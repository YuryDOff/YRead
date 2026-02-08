import { useState } from 'react';
import {
  BookOpen, Wand2, Heart, Rocket, Sword, Star, Feather,
  Loader2,
} from 'lucide-react';
import { useBook } from '../context/BookContext';

const STYLES = [
  { id: 'non_fiction', label: 'Non-Fiction', desc: 'Realistic, documentary', icon: BookOpen },
  { id: 'fiction', label: 'Fiction', desc: 'Versatile, balanced', icon: Wand2 },
  { id: 'romance', label: 'Romance', desc: 'Soft, dreamy', icon: Heart },
  { id: 'sci_fi', label: 'Sci-Fi', desc: 'Futuristic, vibrant', icon: Rocket },
  { id: 'fantasy', label: 'Fantasy', desc: 'Epic, painterly', icon: Sword },
  { id: 'fairy_tale', label: 'Fairy Tale', desc: 'Whimsical, storybook', icon: Star },
  { id: 'classic', label: 'Classic Lit', desc: 'Vintage, engraving-style', icon: Feather },
] as const;

const FREQ_OPTIONS = [
  { value: 2, label: 'Every 2 pages' },
  { value: 4, label: 'Every 4 pages' },
  { value: 8, label: 'Every 8 pages' },
  { value: 12, label: 'Every 12 pages' },
];

interface Props {
  onSubmit: () => void;
  loading?: boolean;
}

export default function StyleSelector({ onSubmit, loading }: Props) {
  const ctx = useBook();
  const totalPages = ctx.book?.total_pages ?? 100;

  const [selected, setSelected] = useState(ctx.styleCategory);
  const [freq, setFreq] = useState(ctx.illustrationFrequency);
  const [layout, setLayout] = useState(ctx.layoutStyle);
  const [wellKnown, setWellKnown] = useState(ctx.isWellKnown);
  const [author, setAuthor] = useState(ctx.authorName);

  const totalIllustrations = Math.max(1, Math.ceil(totalPages / freq));

  function handleSubmit() {
    ctx.setStyleCategory(selected);
    ctx.setIllustrationFrequency(freq);
    ctx.setLayoutStyle(layout);
    ctx.setIsWellKnown(wellKnown);
    ctx.setAuthorName(author);
    onSubmit();
  }

  return (
    <div className="w-full max-w-2xl space-y-8">
      <div className="text-center space-y-1">
        <h2 className="font-display text-3xl font-semibold text-charcoal">
          Customize Your Experience
        </h2>
        <p className="text-sepia font-body text-sm">
          {ctx.book?.title} — {totalPages} pages
        </p>
      </div>

      {/* Book recognition */}
      <section className="space-y-3 p-4 rounded-xl bg-white/50 border border-sepia/15">
        <label className="flex items-center gap-3 cursor-pointer">
          <input
            type="checkbox"
            checked={wellKnown}
            onChange={(e) => setWellKnown(e.target.checked)}
            className="w-4 h-4 accent-golden"
          />
          <span className="font-ui text-sm text-charcoal">
            This is a well-known published book
          </span>
        </label>
        {wellKnown && (
          <input
            value={author}
            onChange={(e) => setAuthor(e.target.value)}
            placeholder="Author name (optional)"
            className="w-full px-3 py-2 rounded-lg border border-sepia/25 bg-white/70
                       font-ui text-sm focus:outline-none focus:ring-2 focus:ring-golden/40"
          />
        )}
        <p className="text-xs text-sepia/70 font-ui">
          This helps find better reference images for characters and locations
        </p>
      </section>

      {/* Visual style */}
      <section className="space-y-3">
        <h3 className="font-display text-lg font-semibold text-charcoal">Visual Style</h3>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
          {STYLES.map(({ id, label, desc, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setSelected(id)}
              className={`flex flex-col items-center gap-2 p-4 rounded-xl border-2 transition-all
                cursor-pointer text-center
                ${selected === id
                  ? 'border-golden bg-golden/10 shadow-sm'
                  : 'border-sepia/15 bg-white/50 hover:border-golden/40'}`}
            >
              <Icon
                size={24}
                className={selected === id ? 'text-golden' : 'text-sepia'}
              />
              <span className="font-ui text-sm font-semibold text-charcoal">{label}</span>
              <span className="font-ui text-xs text-sepia">{desc}</span>
            </button>
          ))}
        </div>
      </section>

      {/* Illustration frequency */}
      <section className="space-y-3">
        <h3 className="font-display text-lg font-semibold text-charcoal">
          Illustration Frequency
        </h3>
        <div className="flex flex-wrap gap-2">
          {FREQ_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => setFreq(opt.value)}
              className={`px-4 py-2 rounded-lg font-ui text-sm transition-all cursor-pointer
                ${freq === opt.value
                  ? 'bg-golden text-paper-cream font-semibold shadow'
                  : 'bg-white/50 border border-sepia/20 text-charcoal hover:border-golden/40'}`}
            >
              {opt.label}
            </button>
          ))}
        </div>
        <p className="text-sm font-ui text-sepia">
          Your book will have ~<strong className="text-charcoal">{totalIllustrations}</strong> illustrations
        </p>
      </section>

      {/* Layout style */}
      <section className="space-y-3">
        <h3 className="font-display text-lg font-semibold text-charcoal">Layout Style</h3>
        <div className="flex gap-3">
          {[
            { id: 'inline_classic', label: 'Inline Classic', desc: 'Traditional illustrated book' },
            { id: 'anime_panels', label: 'Anime Panels', desc: 'Manga-style panels' },
          ].map(({ id, label, desc }) => (
            <button
              key={id}
              onClick={() => setLayout(id)}
              className={`flex-1 p-4 rounded-xl border-2 text-left transition-all cursor-pointer
                ${layout === id
                  ? 'border-golden bg-golden/10'
                  : 'border-sepia/15 bg-white/50 hover:border-golden/40'}`}
            >
              <span className="block font-ui text-sm font-semibold text-charcoal">{label}</span>
              <span className="block font-ui text-xs text-sepia mt-1">{desc}</span>
            </button>
          ))}
        </div>
      </section>

      {/* Submit */}
      <button
        onClick={handleSubmit}
        disabled={loading}
        className="w-full flex items-center justify-center gap-2 px-6 py-3 rounded-lg
                   font-ui font-semibold text-paper-cream bg-midnight
                   hover:bg-midnight/90 disabled:opacity-40 disabled:cursor-not-allowed
                   transition-colors shadow cursor-pointer"
      >
        {loading ? (
          <>
            <Loader2 size={18} className="animate-spin" />
            Analyzing...
          </>
        ) : (
          'Analyze Book'
        )}
      </button>
    </div>
  );
}
