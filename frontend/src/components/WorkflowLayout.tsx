import { useEffect, useState } from 'react';
import { Outlet, useParams, useNavigate } from 'react-router-dom';
import { getBook, getVisualBible } from '../services/api';
import { useBook } from '../context/BookContext';
import WorkflowNav from './WorkflowNav';

export default function WorkflowLayout() {
  const { bookId } = useParams<{ bookId?: string }>();
  const navigate = useNavigate();
  const ctx = useBook();
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!bookId) return;
    if (ctx.book?.id === Number(bookId)) return;
    setLoading(true);
    getBook(Number(bookId))
      .then((b) => {
        ctx.setBook(b);
        if (b.well_known_book_title != null) ctx.setWellKnownBookTitle(b.well_known_book_title);
        if (b.similar_book_title != null) ctx.setSimilarBookTitle(b.similar_book_title);
        return getVisualBible(b.id).catch(() => null);
      })
      .then((data) => {
        if (data?.visual_bible) {
          ctx.setStyleCategory(data.visual_bible.style_category ?? 'fiction');
          if (data.visual_bible.illustration_frequency != null) {
            ctx.setIllustrationFrequency(data.visual_bible.illustration_frequency);
          }
          if (data.visual_bible.layout_style) {
            ctx.setLayoutStyle(data.visual_bible.layout_style);
          }
        }
      })
      .catch(() => navigate('/'))
      .finally(() => setLoading(false));
  }, [bookId, ctx.book?.id, ctx.setBook, ctx.setStyleCategory, ctx.setIllustrationFrequency, ctx.setLayoutStyle, navigate]);

  if (bookId && (loading || (Number(bookId) !== ctx.book?.id && !ctx.book))) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-paper-cream">
        <p className="font-ui text-sepia">Loading book...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-paper-cream flex flex-col">
      <WorkflowNav />
      <main className="flex-1">
        <Outlet />
      </main>
    </div>
  );
}
