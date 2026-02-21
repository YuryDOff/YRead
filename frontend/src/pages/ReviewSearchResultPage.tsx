import { useEffect, useState, useRef } from 'react';
import { useNavigate, useParams, useLocation } from 'react-router-dom';
import { useBook } from '../context/BookContext';
import VisualBibleReview from '../components/VisualBibleReview';
import {
  getVisualBible,
  getReferenceResults,
  getEngineRatings,
  approveVisualBible,
  uploadReferenceImage,
} from '../services/api';
import type { EngineRatingResponse } from '../services/api';
import type { ReferenceImages } from '../services/api';

export default function ReviewSearchResultPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { bookId: bookIdParam } = useParams<{ bookId?: string }>();
  const ctx = useBook();
  const bookId = ctx.book?.id ?? (bookIdParam ? Number(bookIdParam) : undefined);
  const initialTab = (location.state as { initialTab?: 'characters' | 'locations' } | null)?.initialTab ?? 'characters';

  const [loading, setLoading] = useState(true);
  const [approving, setApproving] = useState(false);
  const [referenceImages, setReferenceImages] = useState<ReferenceImages | null>(null);
  const [engineRatings, setEngineRatings] = useState<EngineRatingResponse[]>([]);
  const uploadInputRef = useRef<HTMLInputElement | null>(null);
  const pendingUpload = useRef<{ entityType: 'character' | 'location'; entityId: number } | null>(null);

  useEffect(() => {
    if (!bookId) {
      navigate('/');
      return;
    }

    (async () => {
      try {
        const [vbData, refResults, ratings] = await Promise.all([
          getVisualBible(bookId),
          getReferenceResults(bookId).catch(() => ({ characters: {}, locations: {} })),
          getEngineRatings(bookId).catch(() => []),
        ]);
        ctx.setVisualBible(vbData.visual_bible);
        ctx.setCharacters(vbData.characters);
        ctx.setLocations(vbData.locations);
        setEngineRatings(Array.isArray(ratings) ? ratings : []);

        const hasStored = Object.keys(refResults.characters).length > 0 || Object.keys(refResults.locations).length > 0;
        if (hasStored) {
          setReferenceImages(refResults);
        } else if (ctx.referenceImages) {
          setReferenceImages(ctx.referenceImages);
        } else {
          setReferenceImages({ characters: {}, locations: {} });
        }
      } catch {
        navigate(bookId ? `/books/${bookId}/review-search` : '/');
      } finally {
        setLoading(false);
      }
    })();
  }, [bookId]); // eslint-disable-line react-hooks/exhaustive-deps

  async function handleApprove(
    charSel: Record<number, string[]>,
    locSel: Record<number, string[]>,
  ) {
    if (!bookId) return;
    setApproving(true);
    try {
      await approveVisualBible(bookId, {
        character_selections: Object.fromEntries(
          Object.entries(charSel).map(([k, v]) => [String(k), Array.isArray(v) && v.length ? v : []])
        ),
        location_selections: Object.fromEntries(
          Object.entries(locSel).map(([k, v]) => [String(k), Array.isArray(v) && v.length ? v : []])
        ),
      });
      navigate(`/books/${bookId}/visual-bible`);
    } catch (err) {
      console.error('Approval failed', err);
    } finally {
      setApproving(false);
    }
  }

  function handleUploadClick(entityType: 'character' | 'location', entityId: number) {
    pendingUpload.current = { entityType, entityId };
    uploadInputRef.current?.click();
  }

  async function handleUploadFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    const { entityType, entityId } = pendingUpload.current ?? {};
    if (!file || !bookId || !entityType || !entityId) {
      e.target.value = '';
      return;
    }
    pendingUpload.current = null;
    e.target.value = '';
    try {
      const result = await uploadReferenceImage(bookId, entityType, entityId, file);
      setReferenceImages((prev) => {
        if (!prev) return prev;
        const key = entityType === 'character'
          ? ctx.characters.find((c) => c.id === entityId)?.name
          : ctx.locations.find((l) => l.id === entityId)?.name;
        if (!key) return prev;
        if (entityType === 'character') {
          const chars = { ...prev.characters, [key]: [...(prev.characters[key] ?? []), result] };
          return { ...prev, characters: chars };
        }
        const locs = { ...prev.locations, [key]: [...(prev.locations[key] ?? []), result] };
        return { ...prev, locations: locs };
      });
    } catch (err) {
      console.error('Upload failed', err);
    }
  }

  if (!bookId) return null;

  if (loading) {
    return (
      <div className="min-h-screen bg-paper-cream flex items-center justify-center">
        <p className="font-ui text-sepia">Loading reference results...</p>
      </div>
    );
  }

  if (!ctx.visualBible) {
    return (
      <div className="min-h-screen bg-paper-cream flex flex-col items-center justify-center gap-4">
        <p className="font-ui text-sepia">No visual bible found. Run analysis first.</p>
        <button
          onClick={() => navigate(`/books/${bookId}/review-search`)}
          className="px-4 py-2 rounded-lg font-ui text-sm text-paper-cream bg-midnight cursor-pointer"
        >
          Back to Search
        </button>
      </div>
    );
  }

  return (
    <>
      <input
        ref={uploadInputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp"
        className="hidden"
        onChange={handleUploadFile}
      />
      <div className="min-h-screen bg-paper-cream flex justify-center px-4 py-12">
        <VisualBibleReview
          characters={ctx.characters}
          locations={ctx.locations}
          visualBible={ctx.visualBible}
          referenceImages={referenceImages}
          engineRatings={engineRatings}
          onRatingUpdate={() => bookId && getEngineRatings(bookId).then(setEngineRatings).catch(() => {})}
          onApprove={handleApprove}
          loading={approving}
          pageTitle="Review Search Result"
          pageDescription="Select reference images for your characters and locations from search results or your uploads. You can select multiple images per entity."
          bookId={bookId}
          onUploadImage={handleUploadClick}
          initialTab={initialTab}
        />
      </div>
    </>
  );
}
