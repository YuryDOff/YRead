import { useBook } from '../context/BookContext';

export default function MoodBoardPage() {
  const { book } = useBook();
  return (
    <div className="p-6">
      <h1 className="text-2xl font-semibold mb-3">Mood Board</h1>
      <p className="text-sm text-gray-600">Book ID: {book?.id ?? '—'}</p>
      <div className="mt-4 rounded border p-4">Reference style summary and entity tabs will appear here.</div>
    </div>
  );
}
