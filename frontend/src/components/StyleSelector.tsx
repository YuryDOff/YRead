import { useState, useEffect } from 'react';
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
  { id: 'cyberpunk', label: 'Cyberpunk', desc: 'Neon, tech-noir', icon: Rocket },
  { id: 'space_opera', label: 'Space Opera', desc: 'Epic space, cosmic', icon: Rocket },
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
  const [wellKnownTitle, setWellKnownTitle] = useState(ctx.wellKnownBookTitle);
  const [hasSimilarBook, setHasSimilarBook] = useState(!!ctx.similarBookTitle);
  const [similarBookTitle, setSimilarBookTitle] = useState(ctx.similarBookTitle);
  const [mainOnly, setMainOnly] = useState(ctx.mainOnlyReferences);
  const [sceneCount, setSceneCount] = useState(ctx.sceneCount);

  // Sync from context when VB loads (e.g. opening existing book)
  useEffect(() => {
    if (ctx.book) {
      setSelected(ctx.styleCategory);
      setFreq(ctx.illustrationFrequency);
      setLayout(ctx.layoutStyle);
      setWellKnown(ctx.isWellKnown);
      setAuthor(ctx.authorName);
      setWellKnownTitle(ctx.wellKnownBookTitle);
      setHasSimilarBook(!!ctx.similarBookTitle);
      setSimilarBookTitle(ctx.similarBookTitle);
      setMainOnly(ctx.mainOnlyReferences);
      setSceneCount(ctx.sceneCount);
    }
  }, [ctx.book?.id, ctx.styleCategory, ctx.illustrationFrequency, ctx.layoutStyle, ctx.isWellKnown, ctx.authorName, ctx.wellKnownBookTitle, ctx.similarBookTitle, ctx.mainOnlyReferences, ctx.sceneCount]);

  const totalIllustrations = Math.max(1, Math.ceil(totalPages / freq));

  function handleSubmit() {
    ctx.setStyleCategory(selected);
    ctx.setIllustrationFrequency(freq);
    ctx.setLayoutStyle(layout);
    ctx.setIsWellKnown(wellKnown);
    ctx.setAuthorName(author);
    ctx.setWellKnownBookTitle(wellKnownTitle);
    ctx.setSimilarBookTitle(hasSimilarBook ? similarBookTitle : '');
    ctx.setMainOnlyReferences(mainOnly);
    ctx.setSceneCount(sceneCount);
    onSubmit();
  }

  return (
    <div className="w-full max-w-2xl space-y-8">
      <div className="text-center space-y-1">
        <h2 className="font-display text-3xl font-semibold text-charcoal">
          Key Parameters
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
          <div className="space-y-2">
            <input
              value={author}
              onChange={(e) => setAuthor(e.target.value)}
              placeholder="Author name (optional)"
              className="w-full px-3 py-2 rounded-lg border border-sepia/25 bg-white/70
                         font-ui text-sm focus:outline-none focus:ring-2 focus:ring-golden/40"
            />
            <input
              value={wellKnownTitle}
              onChange={(e) => setWellKnownTitle(e.target.value)}
              placeholder="Title of the book (e.g. A Study in Scarlet)"
              className="w-full px-3 py-2 rounded-lg border border-sepia/25 bg-white/70
                         font-ui text-sm focus:outline-none focus:ring-2 focus:ring-golden/40"
            />
          </div>
        )}
        <p className="text-xs text-sepia/70 font-ui">
          This helps find better reference images for characters and locations
        </p>

        <div className="border-t border-sepia/10 pt-3 mt-1">
          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={hasSimilarBook}
              onChange={(e) => setHasSimilarBook(e.target.checked)}
              className="w-4 h-4 accent-golden"
            />
            <span className="font-ui text-sm text-charcoal">
              Is there another book like it?
            </span>
          </label>
          {hasSimilarBook && (
            <input
              value={similarBookTitle}
              onChange={(e) => setSimilarBookTitle(e.target.value)}
              placeholder="Enter similar book title (helps with visual style)"
              className="w-full mt-2 px-3 py-2 rounded-lg border border-sepia/25 bg-white/70
                         font-ui text-sm focus:outline-none focus:ring-2 focus:ring-golden/40"
            />
          )}
        </div>

        <div className="border-t border-sepia/10 pt-3 mt-1">
          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={mainOnly}
              onChange={(e) => setMainOnly(e.target.checked)}
              className="w-4 h-4 accent-golden"
            />
            <span className="font-ui text-sm text-charcoal">
              Limit reference search to main character & location only
            </span>
          </label>
          <p className="text-xs text-sepia/70 font-ui mt-1 ml-7">
            Saves search API quota. Other characters/locations will use a placeholder image.
          </p>
        </div>
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

      {/* Scene count */}
      <section className="space-y-3">
        <h3 className="font-display text-lg font-semibold text-charcoal">Key Scenes to Extract</h3>
        <div className="flex items-center gap-4">
          <input
            type="number"
            min={3}
            max={20}
            value={sceneCount}
            onChange={(e) => setSceneCount(Math.min(20, Math.max(3, Number(e.target.value))))}
            className="w-24 px-3 py-2 rounded-lg border border-sepia/20 bg-white font-ui text-sm
                       text-charcoal focus:outline-none focus:ring-2 focus:ring-golden/40"
          />
          <p className="text-sm font-ui text-sepia">
            scenes (3–20) — key narrative moments to illustrate
          </p>
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
