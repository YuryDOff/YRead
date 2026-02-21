import { useLocation, useNavigate, useParams } from 'react-router-dom';
import { ChevronRight } from 'lucide-react';
import { useBook } from '../context/BookContext';

const WORKFLOW_STAGES: { segment: string; label: string }[] = [
  { segment: 'manuscript-upload', label: 'Upload manuscript' },
  { segment: 'analysis-review', label: 'Analysis Review' },
  { segment: 'review-search', label: 'Search Queries' },
  { segment: 'review-search-result', label: 'Search Results' },
  { segment: 'visual-bible', label: 'Visual Bible' },
  { segment: 'preview', label: 'Preview' },
];

function isCurrentSegment(segment: string, locationPath: string, bookId?: string): boolean {
  if (segment === 'preview') {
    if (bookId) return locationPath === `/books/${bookId}/preview`;
    return locationPath === '/preview';
  }
  if (segment === 'review-search-result') {
    if (bookId) return locationPath === `/books/${bookId}/review-search-result`;
    return locationPath === '/review-search-result';
  }
  if (bookId) return locationPath === `/books/${bookId}/${segment}`;
  return locationPath === `/${segment}`;
}

export default function WorkflowNav() {
  const location = useLocation();
  const navigate = useNavigate();
  const { bookId } = useParams<{ bookId?: string }>();
  const ctx = useBook();
  const hasBook = !!ctx.book;

  const effectiveBookId = bookId ?? (hasBook && ctx.book ? String(ctx.book.id) : undefined);
  const href = (segment: string) =>
    effectiveBookId ? `/books/${effectiveBookId}/${segment}` : segment === 'manuscript-upload' ? '/manuscript-upload' : '#';

  return (
    <nav
      className="w-full border-b border-sepia/15 bg-white/50 px-4 py-3"
      aria-label="Workflow stages"
    >
      <div className="max-w-4xl mx-auto flex flex-wrap items-center gap-1 gap-y-2">
        <a
          href="/"
          onClick={(e) => { e.preventDefault(); navigate('/'); }}
          className="font-ui text-sm px-1.5 py-0.5 rounded text-sepia hover:text-charcoal hover:bg-sepia/10 transition-colors cursor-pointer mr-2"
        >
          Dashboard
        </a>
        <ChevronRight size={14} className="text-sepia/40 flex-shrink-0" aria-hidden />
        {WORKFLOW_STAGES.map((stage, i) => {
          const isCurrent = isCurrentSegment(stage.segment, location.pathname, bookId);
          const canNavigate = hasBook || stage.segment === 'manuscript-upload';

          if (!hasBook && stage.segment !== 'manuscript-upload') {
            return null;
          }

          return (
            <span key={stage.segment} className="flex items-center gap-1">
              {i > 0 && (
                <ChevronRight
                  size={14}
                  className="text-sepia/40 flex-shrink-0"
                  aria-hidden
                />
              )}
              {canNavigate ? (
                <button
                  type="button"
                  onClick={() => navigate(href(stage.segment))}
                  className={`font-ui text-sm px-1.5 py-0.5 rounded transition-colors cursor-pointer ${
                    isCurrent
                      ? 'text-midnight font-semibold underline decoration-golden underline-offset-2'
                      : 'text-sepia hover:text-charcoal hover:bg-sepia/10'
                  }`}
                  aria-current={isCurrent ? 'page' : undefined}
                >
                  {stage.label}
                </button>
              ) : (
                <span
                  className={`font-ui text-sm px-1.5 py-0.5 ${
                    isCurrent ? 'text-midnight font-semibold' : 'text-sepia/60'
                  }`}
                >
                  {stage.label}
                </span>
              )}
            </span>
          );
        })}
      </div>
    </nav>
  );
}
