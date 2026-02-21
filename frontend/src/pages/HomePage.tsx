import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Dialog, DialogPanel, DialogTitle, Menu, MenuButton, MenuItem, MenuItems } from '@headlessui/react';
import { BookOpen, Sparkles, Palette, Wand2, ChevronRight, Trash2, MoreVertical, Settings } from 'lucide-react';
import { listBooks, deleteBook, type Book } from '../services/api';
import { useBook } from '../context/BookContext';

const WORKFLOW_STAGE_LINKS: { segment: string; label: string }[] = [
  { segment: 'preview', label: 'Preview' },
  { segment: 'analysis-review', label: 'Analysis Review' },
  { segment: 'review-search', label: 'Search Queries' },
  { segment: 'review-search-result', label: 'Search Results' },
  { segment: 'visual-bible', label: 'Visual Bible' },
  { segment: 'manuscript-upload', label: 'Upload manuscript' },
];

export default function HomePage() {
  const navigate = useNavigate();
  const ctx = useBook();
  const [readyBooks, setReadyBooks] = useState<Book[]>([]);
  const [booksLoading, setBooksLoading] = useState(true);
  const [booksError, setBooksError] = useState<string | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Book | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const loadBooks = () => {
    setBooksLoading(true);
    setBooksError(null);
    listBooks()
      .then((books) => {
        setReadyBooks(books);
      })
      .catch((err) => {
        const msg = err?.response?.data?.detail ?? err?.message ?? 'Request failed';
        setBooksError(typeof msg === 'string' ? msg : 'Failed to load books');
        setReadyBooks([]);
      })
      .finally(() => {
        setBooksLoading(false);
      });
  };

  useEffect(() => {
    loadBooks();
  }, []);

  function handleCreateCover(book: Book) {
    ctx.setBook(book);
    navigate(`/books/${book.id}/preview`);
  }

  function openWorkflowStage(book: Book, segment: string) {
    ctx.setBook(book);
    navigate(`/books/${book.id}/${segment}`);
  }

  function openDeleteDialog(e: React.MouseEvent, book: Book) {
    e.stopPropagation();
    setDeleteError(null);
    setDeleteTarget(book);
  }

  function closeDeleteDialog() {
    setDeleteTarget(null);
    setDeleteError(null);
  }

  async function confirmDelete() {
    if (!deleteTarget) return;
    try {
      await deleteBook(deleteTarget.id);
      setReadyBooks((prev) => prev.filter((b) => b.id !== deleteTarget.id));
      closeDeleteDialog();
    } catch {
      setDeleteError('Failed to delete the book. Please try again.');
    }
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4 bg-paper-cream relative">
      {/* Settings button */}
      <button
        type="button"
        onClick={() => navigate('/settings')}
        className="absolute top-4 right-4 p-2 rounded-lg text-sepia/60 hover:text-golden
                   hover:bg-sepia/10 transition-colors cursor-pointer"
        title="Settings"
      >
        <Settings size={22} />
      </button>

      {/* Hero */}
      <div className="max-w-2xl text-center space-y-8">
        <h1 className="font-display text-5xl md:text-6xl font-bold text-charcoal leading-tight">
          StoryForge<br />
          <span className="text-golden">AI</span>
        </h1>

        <p className="font-body text-lg text-sepia max-w-lg mx-auto leading-relaxed">
          Create professional book covers and illustrated interior pages for KDP publishing. 
          AI-powered visual storytelling for independent authors.
        </p>

        {/* Feature pills */}
        <div className="flex flex-wrap justify-center gap-3 pt-4">
          {[
            { icon: BookOpen, label: 'Upload your manuscript' },
            { icon: Sparkles, label: 'AI Analysis' },
            { icon: Palette, label: 'Custom illustrations' },
            { icon: Wand2, label: 'KDP-ready covers' },
          ].map(({ icon: Icon, label }) => (
            <div
              key={label}
              className="flex items-center gap-2 px-4 py-2.5 rounded-full
                         bg-white/70 border border-sepia/25 text-charcoal text-sm font-ui
                         hover:border-golden/50 hover:bg-white/90 transition-all shadow-sm"
            >
              <Icon size={18} className="text-golden flex-shrink-0" />
              {label}
            </div>
          ))}
        </div>

        {/* CTA */}
        <button
          onClick={() => { ctx.reset(); navigate('/manuscript-upload'); }}
          className="mt-4 px-8 py-3.5 rounded-lg font-ui font-semibold text-paper-cream
                     bg-midnight hover:bg-midnight/90 transition-colors shadow-md
                     hover:shadow-lg cursor-pointer"
        >
          Create Your Book Cover
        </button>
      </div>

      {/* Your Recent Projects section – always show so loading/error is visible */}
      <div className="w-full max-w-2xl mt-16 space-y-4">
        <h2 className="font-display text-xl font-semibold text-charcoal text-center">
          Your Recent Projects
        </h2>

        {booksLoading && (
          <p className="font-ui text-sm text-sepia text-center py-4">
            Loading…
          </p>
        )}
        {!booksLoading && booksError && (
          <div className="text-center py-4 space-y-2">
            <p className="font-ui text-sm text-dusty-rose">
              {booksError}
            </p>
            <button
              type="button"
              onClick={loadBooks}
              className="px-4 py-2 rounded-lg font-ui text-sm font-semibold text-paper-cream
                         bg-midnight hover:bg-midnight/90 transition-colors cursor-pointer"
            >
              Retry
            </button>
          </div>
        )}
        {!booksLoading && !booksError && readyBooks.length === 0 && (
          <p className="font-ui text-sm text-sepia text-center py-4">
            No projects yet. Create your first book above.
          </p>
        )}
        {!booksLoading && !booksError && readyBooks.length > 0 && (
          <div className="space-y-3">
            {readyBooks.map((book) => (
              <div
                key={book.id}
                onClick={() => handleCreateCover(book)}
                className="w-full flex items-center justify-between p-4 rounded-xl
                           bg-white/60 border border-sepia/15 hover:border-golden/40
                           hover:shadow-md transition-all cursor-pointer text-left group"
              >
                <div className="space-y-0.5">
                  <span className="block font-display text-base font-semibold text-charcoal
                                   group-hover:text-midnight transition-colors">
                    {book.title}
                  </span>
                  <span className="block font-ui text-xs text-sepia">
                    {book.total_pages ?? '?'} pages
                    {book.author ? ` · ${book.author}` : ''}
                  </span>
                </div>

                <div className="flex items-center gap-1">
                  <Menu as="div" className="relative">
                    <MenuButton
                      onClick={(e) => e.stopPropagation()}
                      title="Open workflow stage"
                      className="p-1.5 rounded-lg text-sepia/40 hover:text-golden
                                 hover:bg-sepia/10 transition-colors cursor-pointer"
                    >
                      <MoreVertical size={16} />
                    </MenuButton>
                    <MenuItems
                      anchor="bottom end"
                      className="mt-1 w-48 rounded-lg bg-white border border-sepia/20 shadow-lg
                                 py-1 font-ui text-sm text-charcoal focus:outline-none z-50"
                    >
                      {WORKFLOW_STAGE_LINKS.map(({ segment, label }) => (
                        <MenuItem key={segment}>
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              openWorkflowStage(book, segment);
                            }}
                            className="w-full text-left px-3 py-2 hover:bg-sepia/10 data-[focus]:bg-sepia/10"
                          >
                            {label}
                          </button>
                        </MenuItem>
                      ))}
                    </MenuItems>
                  </Menu>
                  <button
                    onClick={(e) => openDeleteDialog(e, book)}
                    title="Delete book and all data"
                    className="p-1.5 rounded-lg text-sepia/40 hover:text-red-500
                               hover:bg-red-50 transition-colors cursor-pointer"
                  >
                    <Trash2 size={16} />
                  </button>
                  <ChevronRight size={18} className="text-sepia group-hover:text-golden transition-colors" />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Delete confirmation dialog */}
      <Dialog open={!!deleteTarget} onClose={closeDeleteDialog} className="relative z-50">
        <div className="fixed inset-0 bg-charcoal/30" aria-hidden="true" />
        <div className="fixed inset-0 flex items-center justify-center p-4">
          <DialogPanel className="w-full max-w-md rounded-xl bg-paper-cream border border-sepia/20
                                 shadow-xl p-6 space-y-4">
            <DialogTitle className="font-display text-lg font-semibold text-charcoal">
              Delete book
            </DialogTitle>
            <p className="font-body text-sepia text-sm">
              Delete &quot;{deleteTarget?.title}&quot; and all its data? This cannot be undone.
            </p>
            {deleteError && (
              <p className="font-ui text-sm text-dusty-rose">
                {deleteError}
              </p>
            )}
            <div className="flex justify-end gap-3 pt-2">
              <button
                onClick={closeDeleteDialog}
                className="px-4 py-2 rounded-lg font-ui text-sm text-charcoal
                           bg-white/80 border border-sepia/25 hover:border-golden/40
                           transition-colors cursor-pointer"
              >
                Cancel
              </button>
              <button
                onClick={confirmDelete}
                className="px-4 py-2 rounded-lg font-ui text-sm font-semibold text-paper-cream
                           bg-midnight hover:bg-midnight/90 transition-colors cursor-pointer"
              >
                Delete
              </button>
            </div>
          </DialogPanel>
        </div>
      </Dialog>
    </div>
  );
}
