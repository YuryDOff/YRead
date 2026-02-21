import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Loader2 } from 'lucide-react';
import {
  getProvidersStatus,
  getEngineRatings,
  listBooks,
  ENABLED_PROVIDERS_STORAGE_KEY,
  type ProviderStatus,
  type EngineRatingResponse,
  type Book,
} from '../services/api';

export default function SettingsPage() {
  const navigate = useNavigate();
  const [providers, setProviders] = useState<ProviderStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [enabled, setEnabled] = useState<Record<string, boolean>>({});
  const [books, setBooks] = useState<Book[]>([]);
  const [selectedBookId, setSelectedBookId] = useState<number | ''>('');
  const [ratings, setRatings] = useState<EngineRatingResponse[]>([]);
  const [ratingsLoading, setRatingsLoading] = useState(false);

  useEffect(() => {
    getProvidersStatus()
      .then((list) => {
        setProviders(list);
        try {
          const raw = localStorage.getItem(ENABLED_PROVIDERS_STORAGE_KEY);
          const stored: string[] = raw ? JSON.parse(raw) : [];
          const map: Record<string, boolean> = {};
          if (Array.isArray(stored) && stored.length > 0) {
            list.forEach((p) => { map[p.name] = stored.includes(p.name); });
          } else {
            list.forEach((p) => { map[p.name] = p.available; });
          }
          setEnabled(map);
        } catch {
          const defaultEnabled: Record<string, boolean> = {};
          list.forEach((p) => { defaultEnabled[p.name] = p.available; });
          setEnabled(defaultEnabled);
        }
      })
      .catch(() => setProviders([]))
      .finally(() => setLoading(false));

    listBooks().then(setBooks).catch(() => setBooks([]));
  }, []);

  useEffect(() => {
    if (selectedBookId === '') {
      setRatings([]);
      return;
    }
    setRatingsLoading(true);
    getEngineRatings(selectedBookId)
      .then(setRatings)
      .catch(() => setRatings([]))
      .finally(() => setRatingsLoading(false));
  }, [selectedBookId]);

  const handleToggle = (name: string, checked: boolean) => {
    const next = { ...enabled, [name]: checked };
    setEnabled(next);
    const list = Object.entries(next).filter(([, v]) => v).map(([k]) => k);
    try {
      localStorage.setItem(ENABLED_PROVIDERS_STORAGE_KEY, JSON.stringify(list));
    } catch {
      // ignore
    }
  };

  return (
    <div className="min-h-screen bg-paper-cream px-4 py-12">
      <div className="max-w-2xl mx-auto space-y-8">
        <div className="flex items-center gap-4">
          <button
            type="button"
            onClick={() => navigate('/')}
            className="p-2 rounded-lg text-sepia hover:text-golden hover:bg-sepia/10 transition-colors"
            title="Back to Dashboard"
          >
            <ArrowLeft size={20} />
          </button>
          <h1 className="font-display text-2xl font-semibold text-charcoal">
            Settings
          </h1>
        </div>

        {/* Reference image search engines */}
        <section className="p-4 rounded-xl bg-white/60 border border-sepia/15 space-y-3">
          <h2 className="font-display text-lg font-semibold text-charcoal">
            Reference image search engines
          </h2>
          <p className="font-ui text-xs text-sepia">
            Choose which engines to use when searching for reference images. Only available (configured) engines can be enabled.
          </p>
          {loading ? (
            <p className="font-ui text-sm text-sepia flex items-center gap-2">
              <Loader2 size={16} className="animate-spin" />
              Loading…
            </p>
          ) : (
            <ul className="space-y-2">
              {providers.map((p) => (
                <li key={p.name} className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    id={`provider-${p.name}`}
                    checked={enabled[p.name] ?? p.available}
                    onChange={(e) => handleToggle(p.name, e.target.checked)}
                    disabled={!p.available}
                    className="w-4 h-4 accent-golden"
                  />
                  <label
                    htmlFor={`provider-${p.name}`}
                    className={`font-ui text-sm ${p.available ? 'text-charcoal cursor-pointer' : 'text-sepia/60'}`}
                  >
                    {p.label}
                    {p.available ? (
                      <span className="ml-2 text-xs text-sepia">Available</span>
                    ) : (
                      <span className="ml-2 text-xs text-sepia/60">Not configured</span>
                    )}
                  </label>
                </li>
              ))}
            </ul>
          )}
        </section>

        {/* Engine ratings (per book) */}
        <section className="p-4 rounded-xl bg-white/60 border border-sepia/15 space-y-3">
          <h2 className="font-display text-lg font-semibold text-charcoal">
            Engine ratings
          </h2>
          <p className="font-ui text-xs text-sepia">
            Likes and dislikes per search engine for a selected book (from the Review Search Result page).
          </p>
          <div>
            <label className="block font-ui text-xs text-sepia uppercase tracking-wide mb-1">
              Show ratings for book
            </label>
            <select
              value={selectedBookId}
              onChange={(e) => setSelectedBookId(e.target.value === '' ? '' : Number(e.target.value))}
              className="w-full max-w-xs px-3 py-2 rounded-lg border border-sepia/20 font-ui text-sm text-charcoal bg-white"
            >
              <option value="">Select a book…</option>
              {books.map((b) => (
                <option key={b.id} value={b.id}>{b.title}</option>
              ))}
            </select>
          </div>
          {ratingsLoading && (
            <p className="font-ui text-sm text-sepia flex items-center gap-2">
              <Loader2 size={16} className="animate-spin" />
              Loading ratings…
            </p>
          )}
          {!ratingsLoading && selectedBookId !== '' && (
            <div className="overflow-x-auto">
              <table className="w-full font-ui text-sm text-left border-collapse">
                <thead>
                  <tr className="border-b border-sepia/20">
                    <th className="py-2 pr-4 text-charcoal font-semibold">Provider</th>
                    <th className="py-2 px-4 text-charcoal font-semibold">Likes</th>
                    <th className="py-2 pl-4 text-charcoal font-semibold">Dislikes</th>
                  </tr>
                </thead>
                <tbody>
                  {ratings.length === 0 ? (
                    <tr>
                      <td colSpan={3} className="py-4 text-sepia text-center">
                        No ratings yet for this book.
                      </td>
                    </tr>
                  ) : (
                    ratings.map((r) => (
                      <tr key={r.provider} className="border-b border-sepia/10">
                        <td className="py-2 pr-4 text-charcoal">{r.provider}</td>
                        <td className="py-2 px-4 text-green-600">{r.likes}</td>
                        <td className="py-2 pl-4 text-red-600">{r.dislikes}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
