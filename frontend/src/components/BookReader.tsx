import { useState, useEffect, useCallback, useRef } from 'react';
import {
  ChevronLeft,
  ChevronRight,
  Home,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { getChunks, getProgress, updateProgress, type Chunk } from '../services/api';
import { useBook } from '../context/BookContext';

/** Approximate words that fit on one rendered page. */
const WORDS_PER_PAGE = 280;

interface Page {
  number: number;
  text: string;
}

export default function BookReader() {
  const { book } = useBook();
  const navigate = useNavigate();
  const bookId = book?.id;

  const [pages, setPages] = useState<Page[]>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const saveTimer = useRef<ReturnType<typeof setInterval> | null>(null);

  // ---- Load chunks and paginate ----
  useEffect(() => {
    if (!bookId) return;
    (async () => {
      const [chunks, progress] = await Promise.all([
        getChunks(bookId),
        getProgress(bookId),
      ]);

      const pgs = paginateChunks(chunks);
      setPages(pgs);
      setTotalPages(pgs.length);
      if (progress.current_page > 1 && progress.current_page <= pgs.length) {
        setCurrentPage(progress.current_page);
      }
    })();
  }, [bookId]);

  // ---- Persist progress every 10 s ----
  useEffect(() => {
    if (!bookId) return;
    saveTimer.current = setInterval(() => {
      updateProgress(bookId, currentPage).catch(() => {});
    }, 10_000);
    return () => {
      if (saveTimer.current) clearInterval(saveTimer.current);
    };
  }, [bookId, currentPage]);

  // ---- Keyboard navigation ----
  const goNext = useCallback(() => {
    setCurrentPage((p) => Math.min(p + 2, totalPages));
  }, [totalPages]);

  const goPrev = useCallback(() => {
    setCurrentPage((p) => Math.max(p - 2, 1));
  }, []);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === 'ArrowRight') goNext();
      if (e.key === 'ArrowLeft') goPrev();
    }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [goNext, goPrev]);

  if (!bookId || pages.length === 0) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-paper-cream">
        <p className="font-ui text-sepia">Loading book...</p>
      </div>
    );
  }

  const leftPage = pages[currentPage - 1] ?? null;
  const rightPage = pages[currentPage] ?? null;
  const progress = totalPages > 0 ? ((currentPage + 1) / totalPages) * 100 : 0;

  return (
    <div className="min-h-screen bg-paper-cream flex flex-col">
      {/* Top bar */}
      <header className="flex items-center justify-between px-6 py-3 border-b border-sepia/15">
        <button
          onClick={() => navigate('/')}
          className="flex items-center gap-1.5 text-sepia hover:text-charcoal
                     font-ui text-sm transition-colors cursor-pointer"
        >
          <Home size={16} />
          Exit
        </button>
        <span className="font-display text-sm text-charcoal font-semibold truncate max-w-xs">
          {book?.title}
        </span>
        <span className="font-ui text-xs text-sepia">
          {Math.min(currentPage + 1, totalPages)} / {totalPages}
        </span>
      </header>

      {/* Book spread */}
      <main className="flex-1 flex items-center justify-center px-4 py-6">
        <div className="flex w-full max-w-5xl shadow-xl rounded-sm overflow-hidden">
          {/* Left page */}
          <PageView page={leftPage} side="left" />
          {/* Spine */}
          <div className="w-px bg-sepia/20" />
          {/* Right page */}
          <PageView page={rightPage} side="right" />
        </div>
      </main>

      {/* Controls */}
      <footer className="px-6 py-3 border-t border-sepia/15 space-y-2">
        {/* Progress bar */}
        <div className="w-full h-1 rounded-full bg-sepia/10 overflow-hidden">
          <div
            className="h-full bg-golden transition-all duration-300"
            style={{ width: `${Math.min(progress, 100)}%` }}
          />
        </div>

        <div className="flex items-center justify-between">
          <button
            onClick={goPrev}
            disabled={currentPage <= 1}
            className="flex items-center gap-1 px-3 py-1.5 rounded-lg font-ui text-sm
                       text-sepia hover:text-charcoal disabled:opacity-30
                       transition-colors cursor-pointer disabled:cursor-not-allowed"
          >
            <ChevronLeft size={16} />
            Previous
          </button>

          <span className="font-ui text-xs text-sepia">
            {Math.round(Math.min(progress, 100))}% complete
          </span>

          <button
            onClick={goNext}
            disabled={currentPage + 1 >= totalPages}
            className="flex items-center gap-1 px-3 py-1.5 rounded-lg font-ui text-sm
                       text-sepia hover:text-charcoal disabled:opacity-30
                       transition-colors cursor-pointer disabled:cursor-not-allowed"
          >
            Next
            <ChevronRight size={16} />
          </button>
        </div>
      </footer>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Page renderer                                                       */
/* ------------------------------------------------------------------ */

function PageView({ page, side }: { page: Page | null; side: 'left' | 'right' }) {
  return (
    <div
      className={`flex-1 min-h-[70vh] p-8 md:p-12 bg-paper-cream
        ${side === 'left' ? 'rounded-l-sm' : 'rounded-r-sm'}`}
    >
      {page ? (
        <>
          <div
            className="font-body text-ink-black text-[15px] leading-[1.75]
                       max-w-[65ch] mx-auto whitespace-pre-wrap text-justify
                       hyphens-auto"
          >
            {page.text}
          </div>
          <p className={`mt-6 font-ui text-xs text-sepia/50
            ${side === 'left' ? 'text-left' : 'text-right'}`}>
            {page.number}
          </p>
        </>
      ) : (
        <div className="flex items-center justify-center h-full text-sepia/30 font-ui text-sm">
          — end —
        </div>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Pagination helper                                                   */
/* ------------------------------------------------------------------ */

function paginateChunks(chunks: Chunk[]): Page[] {
  // Combine all chunk text, then split into pages by word count
  const fullText = chunks.map((c) => c.text).join('\n\n');
  const words = fullText.split(/\s+/);
  const pages: Page[] = [];
  let idx = 0;

  while (idx < words.length) {
    const slice = words.slice(idx, idx + WORDS_PER_PAGE);
    pages.push({
      number: pages.length + 1,
      text: slice.join(' '),
    });
    idx += WORDS_PER_PAGE;
  }

  return pages;
}
