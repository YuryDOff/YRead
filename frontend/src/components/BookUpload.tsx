import { useState } from 'react';
import { Upload, Loader2, CheckCircle2, AlertCircle } from 'lucide-react';
import { importBook, chunkBook, type Book } from '../services/api';

const GDRIVE_RE = /https?:\/\/drive\.google\.com\/file\/d\/[a-zA-Z0-9_-]+/;

interface Props {
  onSuccess: (book: Book) => void;
}

export default function BookUpload({ onSuccess }: Props) {
  const [link, setLink] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [step, setStep] = useState<'idle' | 'importing' | 'chunking' | 'done'>('idle');

  const isValid = GDRIVE_RE.test(link);

  async function handleImport() {
    setError(null);
    setLoading(true);
    try {
      setStep('importing');
      const book = await importBook(link);

      setStep('chunking');
      await chunkBook(book.id);

      setStep('done');
      onSuccess(book);
    } catch (err: unknown) {
      const msg =
        err instanceof Error
          ? err.message
          : 'Something went wrong. Please try again.';
      setError(msg);
      setStep('idle');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="w-full max-w-lg space-y-6">
      <div className="space-y-2 text-center">
        <h2 className="font-display text-3xl font-semibold text-charcoal">
          Import Your Book
        </h2>
        <p className="text-sepia font-body text-sm">
          Paste a Google Drive shareable link to a <strong>.txt</strong> file
        </p>
      </div>

      {/* Input */}
      <div className="space-y-3">
        <div className="relative">
          <input
            type="url"
            value={link}
            onChange={(e) => {
              setLink(e.target.value);
              setError(null);
            }}
            placeholder="https://drive.google.com/file/d/..."
            disabled={loading}
            className="w-full px-4 py-3 pr-10 rounded-lg border border-sepia/30
                       bg-white/70 font-ui text-sm text-ink-black
                       placeholder:text-sepia/50
                       focus:outline-none focus:ring-2 focus:ring-golden/50 focus:border-golden
                       disabled:opacity-50 transition-colors"
          />
          {link && (
            <span className="absolute right-3 top-1/2 -translate-y-1/2">
              {isValid ? (
                <CheckCircle2 size={18} className="text-sage" />
              ) : (
                <AlertCircle size={18} className="text-dusty-rose" />
              )}
            </span>
          )}
        </div>

        {link && !isValid && (
          <p className="text-dusty-rose text-xs font-ui">
            Please enter a valid Google Drive link
            (https://drive.google.com/file/d/…)
          </p>
        )}

        {error && (
          <div className="flex items-start gap-2 p-3 rounded-lg bg-dusty-rose/10 border border-dusty-rose/30">
            <AlertCircle size={16} className="text-dusty-rose mt-0.5 shrink-0" />
            <p className="text-dusty-rose text-xs font-ui">{error}</p>
          </div>
        )}
      </div>

      {/* Status */}
      {loading && (
        <div className="flex items-center gap-3 text-sm font-ui text-charcoal">
          <Loader2 size={18} className="animate-spin text-golden" />
          {step === 'importing' && 'Downloading book from Google Drive...'}
          {step === 'chunking' && 'Processing text into chapters...'}
        </div>
      )}

      {/* Button */}
      <button
        onClick={handleImport}
        disabled={!isValid || loading}
        className="w-full flex items-center justify-center gap-2 px-6 py-3 rounded-lg
                   font-ui font-semibold text-paper-cream
                   bg-midnight hover:bg-midnight/90
                   disabled:opacity-40 disabled:cursor-not-allowed
                   transition-colors shadow cursor-pointer"
      >
        {loading ? (
          <Loader2 size={18} className="animate-spin" />
        ) : (
          <Upload size={18} />
        )}
        {loading ? 'Importing...' : 'Import Book'}
      </button>
    </div>
  );
}
