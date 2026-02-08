import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useBook } from '../context/BookContext';
import BookReader from '../components/BookReader';

export default function ReadingPage() {
  const { book } = useBook();
  const navigate = useNavigate();

  useEffect(() => {
    if (!book) {
      navigate('/setup');
    }
  }, [book, navigate]);

  if (!book) return null;

  return <BookReader />;
}
