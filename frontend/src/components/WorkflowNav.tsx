import { useLocation, useNavigate, useParams } from 'react-router-dom';
import { ChevronRight } from 'lucide-react';
import { useBook } from '../context/BookContext';

const COVER_ONLY_STEPS = [
  { label: 'Upload', path: 'manuscript-upload' },
  { label: 'Characters', path: 'analysis-review' },
  { label: 'Mood Board', path: 'mood-board' },
  { label: 'Cover Brief', path: 'cover-brief' },
  { label: 'Generate', path: 'studio/cover' },
  { label: 'Typography', path: 'studio/text' },
];

const FULL_BOOK_STEPS = [
  { label: 'Upload', path: 'manuscript-upload' },
  { label: 'AI Analysis', path: 'analysis-review' },
  { label: 'Mood Board', path: 'mood-board' },
  { label: 'Cover Brief', path: 'cover-brief' },
  { label: 'Generate', path: 'studio/cover' },
  { label: 'Typography', path: 'studio/text' },
  { label: 'Preview', path: 'preview' },
];

function isCurrentStep(stepPath: string, locationPath: string, bookId?: string): boolean {
  if (stepPath === 'preview') {
    if (bookId) return locationPath === `/books/${bookId}/preview`;
    return locationPath === '/preview';
  }
  if (stepPath === 'studio/cover') {
    if (bookId) return locationPath === `/books/${bookId}/studio/cover`;
    return locationPath.includes('studio/cover');
  }
  if (stepPath === 'studio/text') {
    if (bookId) return locationPath === `/books/${bookId}/studio/text`;
    return locationPath.includes('studio/text');
  }
  if (bookId) return locationPath === `/books/${bookId}/${stepPath}`;
  return locationPath === `/${stepPath}` || (stepPath === 'manuscript-upload' && locationPath === '/manuscript-upload');
}

export default function WorkflowNav() {
  const location = useLocation();
  const navigate = useNavigate();
  const { bookId } = useParams<{ bookId?: string }>();
  const { book, workflowType } = useBook();
  const hasBook = !!book;

  const steps = workflowType === 'cover_only' ? COVER_ONLY_STEPS : FULL_BOOK_STEPS;
  const effectiveBookId = bookId ?? (hasBook && book ? String(book.id) : undefined);

  const goTo = (path: string) => {
    if (path === 'manuscript-upload') {
      navigate(effectiveBookId ? `/books/${effectiveBookId}/manuscript-upload` : '/manuscript-upload');
      return;
    }
    if (effectiveBookId) navigate(`/books/${effectiveBookId}/${path}`);
  };

  return (
    <nav
      className="w-full border-b border-sepia/15 bg-white/50 px-4 py-3"
      aria-label="Workflow steps"
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
        {steps.map((step, i) => {
          const isActive = isCurrentStep(step.path, location.pathname, effectiveBookId ?? undefined);
          const isComplete = false;
          const canNavigate = hasBook || step.path === 'manuscript-upload';

          if (!hasBook && step.path !== 'manuscript-upload') return null;

          return (
            <span key={step.path} className="flex items-center gap-1">
              {i > 0 && <ChevronRight size={14} className="text-sepia/40 flex-shrink-0" aria-hidden />}
              {canNavigate ? (
                <button
                  type="button"
                  onClick={() => goTo(step.path)}
                  aria-current={isActive ? 'step' : undefined}
                  className={[
                    'flex items-center gap-1.5 rounded px-3 py-1.5 text-sm font-medium transition-colors font-ui',
                    isActive ? 'bg-indigo-600 text-white' : 'text-gray-500 hover:text-gray-900',
                    isComplete ? 'text-green-700' : '',
                  ].join(' ')}
                >
                  {isComplete && <span aria-hidden>✓</span>}
                  <span>{step.label}</span>
                </button>
              ) : (
                <span className={`font-ui text-sm px-1.5 py-0.5 ${isActive ? 'text-midnight font-semibold' : 'text-sepia/60'}`}>
                  {step.label}
                </span>
              )}
            </span>
          );
        })}
      </div>
    </nav>
  );
}
