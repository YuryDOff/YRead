import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useBook } from '../context/BookContext';
import { getBook } from '../services/api';
import BookReader from '../components/BookReader';

export default function PreviewPage() {
  const { book, setBook } = useBook();
  const navigate = useNavigate();
  const { bookId } = useParams<{ bookId: string }>();
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Book already in context — nothing to load
    if (book) return;

    // Try to load by URL param
    if (bookId) {
      setLoading(true);
      getBook(Number(bookId))
        .then((b) => {
          setBook(b);
        })
        .catch(() => {
          navigate('/');
        })
        .finally(() => setLoading(false));
      return;
    }

    // No book anywhere — go home
    navigate('/');
  }, [book, bookId, navigate, setBook]);

  if (loading || !book) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-paper-cream">
        <p className="font-ui text-sepia">Loading preview...</p>
      </div>
    );
  }

  return <BookReader />;
}
