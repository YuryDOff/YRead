import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useBook } from '../context/BookContext';
import VisualBibleReview from '../components/VisualBibleReview';
import {
  getVisualBible,
  approveVisualBible,
} from '../services/api';

export default function VisualBiblePage() {
  const navigate = useNavigate();
  const ctx = useBook();
  const bookId = ctx.book?.id;

  const [loading, setLoading] = useState(true);
  const [approving, setApproving] = useState(false);

  // Load visual bible data if not in context
  useEffect(() => {
    if (!bookId) {
      navigate('/setup');
      return;
    }

    (async () => {
      try {
        const data = await getVisualBible(bookId);
        ctx.setVisualBible(data.visual_bible);
        ctx.setCharacters(data.characters);
        ctx.setLocations(data.locations);
      } catch {
        // Visual bible might not exist yet
      } finally {
        setLoading(false);
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [bookId]);

  async function handleApprove(
    charSel: Record<number, string>,
    locSel: Record<number, string>,
  ) {
    if (!bookId) return;
    setApproving(true);
    try {
      await approveVisualBible(bookId, {
        character_selections: charSel,
        location_selections: locSel,
      });
      navigate('/read');
    } catch (err) {
      console.error('Approval failed', err);
    } finally {
      setApproving(false);
    }
  }

  if (!bookId) return null;

  if (loading) {
    return (
      <div className="min-h-screen bg-paper-cream flex items-center justify-center">
        <p className="font-ui text-sepia">Loading visual bible...</p>
      </div>
    );
  }

  if (!ctx.visualBible) {
    return (
      <div className="min-h-screen bg-paper-cream flex flex-col items-center justify-center gap-4">
        <p className="font-ui text-sepia">No visual bible found.</p>
        <button
          onClick={() => navigate('/setup')}
          className="px-4 py-2 rounded-lg font-ui text-sm text-paper-cream bg-midnight cursor-pointer"
        >
          Go to Setup
        </button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-paper-cream flex justify-center px-4 py-12">
      <VisualBibleReview
        characters={ctx.characters}
        locations={ctx.locations}
        visualBible={ctx.visualBible}
        referenceImages={ctx.referenceImages}
        onApprove={handleApprove}
        loading={approving}
      />
    </div>
  );
}
