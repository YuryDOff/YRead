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
  getArtefacts,
  getCoverAnalysis,
  getCharacters,
  getLocations,
} from '../services/api';
import type { EngineRatingResponse, VisualBible } from '../services/api';
import type { ReferenceImages } from '../services/api';
import { getCoverImages } from '../services/api';

function minimalVisualBible(bookId: number): VisualBible {
  return {
    id: 0,
    book_id: bookId,
    style_category: null,
    tone_description: null,
    illustration_frequency: null,
    layout_style: null,
    approved_at: null,
  };
}

export default function ReviewSearchResultPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { bookId: bookIdParam } = useParams<{ bookId?: string }>();
  const ctx = useBook();
  const bookId = ctx.book?.id ?? (bookIdParam ? Number(bookIdParam) : undefined);
  const navState = location.state as { initialTab?: 'characters' | 'locations' | 'artefacts' | 'cover' | 'style'; referenceImages?: ReferenceImages } | null;
  const initialTab = navState?.initialTab ?? 'characters';
  const stateReferenceImages = navState?.referenceImages;

  const [loading, setLoading] = useState(true);
  const [approving, setApproving] = useState(false);
  const [referenceImages, setReferenceImages] = useState<ReferenceImages | null>(() => stateReferenceImages ?? null);
  const [artefacts, setArtefacts] = useState<import('../services/api').Artefact[]>([]);
  const [coverEntityId, setCoverEntityId] = useState<number | null>(null);
  const [engineRatings, setEngineRatings] = useState<EngineRatingResponse[]>([]);
  const uploadInputRef = useRef<HTMLInputElement | null>(null);
  const pendingUpload = useRef<{ entityType: 'character' | 'location' | 'artefact' | 'cover'; entityId: number } | null>(null);

  useEffect(() => {
    if (!bookId) {
      navigate('/');
      return;
    }

    (async () => {
      try {
        const [refResults, ratings, artefactList, coverAnalysis] = await Promise.all([
          getReferenceResults(bookId).catch(() => ({ characters: {}, locations: {}, artefacts: {}, cover: {} })),
          getEngineRatings(bookId).catch(() => []),
          getArtefacts(bookId).catch(() => []),
          getCoverAnalysis(bookId).catch(() => null),
        ]);
        let vbData: { visual_bible: VisualBible; characters: import('../services/api').Character[]; locations: import('../services/api').Location[] };
        try {
          vbData = await getVisualBible(bookId);
        } catch {
          const [chars, locs] = await Promise.all([
            getCharacters(bookId).catch(() => []),
            getLocations(bookId).catch(() => []),
          ]);
          vbData = {
            visual_bible: minimalVisualBible(bookId),
            characters: chars,
            locations: locs,
          };
        }
        ctx.setVisualBible(vbData.visual_bible);
        ctx.setCharacters(vbData.characters);
        ctx.setLocations(vbData.locations);
        setArtefacts(artefactList ?? []);
        setCoverEntityId(coverAnalysis?.id ?? null);
        setEngineRatings(Array.isArray(ratings) ? ratings : []);

        const refCoverCount = getCoverImages(refResults).length;
        const hasStored =
          Object.keys(refResults.characters ?? {}).length > 0 ||
          Object.keys(refResults.locations ?? {}).length > 0 ||
          Object.keys(refResults.artefacts ?? {}).length > 0 ||
          refCoverCount > 0;
        const hasStateRefs =
          stateReferenceImages &&
          (Object.keys(stateReferenceImages.characters ?? {}).length > 0 ||
            Object.keys(stateReferenceImages.locations ?? {}).length > 0 ||
            Object.keys(stateReferenceImages.artefacts ?? {}).length > 0 ||
            getCoverImages(stateReferenceImages).length > 0);
        if (hasStored) {
          setReferenceImages(refResults);
        } else if (hasStateRefs && stateReferenceImages) {
          setReferenceImages(stateReferenceImages);
        } else if (ctx.referenceImages && (Object.keys(ctx.referenceImages.characters ?? {}).length > 0 || Object.keys(ctx.referenceImages.locations ?? {}).length > 0 || getCoverImages(ctx.referenceImages).length > 0)) {
          setReferenceImages(ctx.referenceImages);
        } else if (!referenceImages || (Object.keys(referenceImages.characters ?? {}).length === 0 && Object.keys(referenceImages.locations ?? {}).length === 0 && getCoverImages(referenceImages).length === 0)) {
          setReferenceImages({ characters: {}, locations: {}, artefacts: {}, cover: {} });
        }
      } catch (err) {
        console.error('Review search result load failed', err);
        navigate(bookId ? `/books/${bookId}/review-search` : '/');
      } finally {
        setLoading(false);
      }
    })();
  }, [bookId]); // eslint-disable-line react-hooks/exhaustive-deps

  async function handleApprove(
    charSel: Record<number, string[]>,
    locSel: Record<number, string[]>,
    artefactSelections?: Record<string, string[]>,
    coverSelections?: string[],
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
        ...(artefactSelections ? { artefact_selections: artefactSelections } : {}),
        ...(coverSelections?.length ? { cover_selections: coverSelections } : {}),
      });
      navigate(`/books/${bookId}/visual-bible`);
    } catch (err) {
      console.error('Approval failed', err);
    } finally {
      setApproving(false);
    }
  }

  function handleUploadClick(entityType: 'character' | 'location' | 'artefact' | 'cover', entityId: number) {
    pendingUpload.current = { entityType, entityId };
    uploadInputRef.current?.click();
  }

  async function handleUploadFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    const { entityType, entityId } = pendingUpload.current ?? {};
    if (!file || !bookId || !entityType || entityId === undefined) {
      e.target.value = '';
      return;
    }
    pendingUpload.current = null;
    e.target.value = '';
    try {
      const result = await uploadReferenceImage(bookId, entityType, entityId, file);
      setReferenceImages((prev) => {
        if (!prev) return prev;
        if (entityType === 'character') {
          const key = ctx.characters.find((c) => c.id === entityId)?.name;
          if (!key) return prev;
          const chars = { ...prev.characters, [key]: [...(prev.characters[key] ?? []), result] };
          return { ...prev, characters: chars };
        }
        if (entityType === 'location') {
          const key = ctx.locations.find((l) => l.id === entityId)?.name;
          if (!key) return prev;
          const locs = { ...prev.locations, [key]: [...(prev.locations[key] ?? []), result] };
          return { ...prev, locations: locs };
        }
        if (entityType === 'artefact') {
          const key = artefacts.find((a) => a.id === entityId)?.name;
          if (!key) return prev;
          const art = { ...(prev.artefacts ?? {}), [key]: [...(prev.artefacts?.[key] ?? []), result] };
          return { ...prev, artefacts: art };
        }
        if (entityType === 'cover') {
          const cover = { cover: [...getCoverImages(prev), result] };
          return { ...prev, cover };
        }
        return prev;
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
          artefacts={artefacts}
          visualBible={ctx.visualBible}
          referenceImages={referenceImages}
          engineRatings={engineRatings}
          onRatingUpdate={() => bookId && getEngineRatings(bookId).then(setEngineRatings).catch(() => {})}
          onApprove={handleApprove}
          loading={approving}
          pageTitle="Review Search Result"
          pageDescription="Select reference images for your characters, locations, artefacts, and cover from search results or your uploads."
          bookId={bookId}
          onUploadImage={handleUploadClick}
          coverEntityId={coverEntityId ?? undefined}
          initialTab={initialTab as 'characters' | 'locations' | 'artefacts' | 'cover' | 'style'}
        />
      </div>
    </>
  );
}
