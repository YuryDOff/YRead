import { useNavigate, useParams } from 'react-router-dom';
import { useBook } from '../context/BookContext';
import { ChevronRight } from 'lucide-react';

export default function VisualBiblePage() {
  const navigate = useNavigate();
  const { bookId: bookIdParam } = useParams<{ bookId?: string }>();
  const ctx = useBook();
  const bookId = ctx.book?.id ?? (bookIdParam ? Number(bookIdParam) : undefined);

  if (!bookId) {
    navigate('/');
    return null;
  }

  return (
    <div className="min-h-screen bg-paper-cream flex flex-col items-center justify-center px-4 py-12">
      <div className="max-w-lg text-center space-y-4">
        <h1 className="font-display text-3xl font-semibold text-charcoal">Visual Bible</h1>
        <p className="font-body text-sepia">
          Next step: AI image generation and final visual bible. This screen will host generation controls and the complete visual bible view.
        </p>
        <button
          type="button"
          onClick={() => navigate(`/books/${bookId}/preview`)}
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg font-ui text-sm text-paper-cream bg-midnight hover:bg-midnight/90 cursor-pointer"
        >
          Continue to Preview
          <ChevronRight size={16} />
        </button>
      </div>
    </div>
  );
}
