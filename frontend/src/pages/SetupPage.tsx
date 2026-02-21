import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useBook } from '../context/BookContext';
import BookUpload, { type BookUploadMetadata } from '../components/BookUpload';
import StyleSelector from '../components/StyleSelector';
import LoadingScreen from '../components/LoadingScreen';
import { analyzeBook, type Book } from '../services/api';

/** Map upload genre (Create Book page) to style_category id (StyleSelector / backend). */
function genreToStyleCategory(genre: string): string {
  const map: Record<string, string> = {
    'Science Fiction': 'sci_fi',
    'Fantasy': 'fantasy',
    'Romance': 'romance',
    'Non-Fiction': 'non_fiction',
    "Children's": 'fairy_tale',
    'Horror': 'fiction',
    'Thriller': 'fiction',
    'Mystery': 'fiction',
    'Historical Fiction': 'classic',
    'Literary Fiction': 'classic',
    'Young Adult': 'fiction',
    'Other': 'fiction',
  };
  return map[genre] ?? 'fiction';
}

type Step = 'upload' | 'style' | 'analyzing';

export default function CreateBookPage() {
  const navigate = useNavigate();
  const ctx = useBook();
  const [step, setStep] = useState<Step>(ctx.book ? 'style' : 'upload');
  const [analyzeLoading, setAnalyzeLoading] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useState<{
    currentChunk: number;
    totalChunks: number;
  } | null>(null);

  function handleUploadSuccess(book: Book, metadata?: BookUploadMetadata) {
    ctx.setBook(book);
    if (metadata?.genre) {
      ctx.setStyleCategory(genreToStyleCategory(metadata.genre));
    }
    if (metadata?.author) {
      ctx.setAuthorName(metadata.author);
    }
    setStep('style');
  }

  async function handleAnalyze() {
    if (!ctx.book) return;
    setAnalyzeLoading(true);
    setAnalysisProgress(null);
    setStep('analyzing');
    try {
      await analyzeBook(
        ctx.book.id,
        {
          style_category: ctx.styleCategory,
          illustration_frequency: ctx.illustrationFrequency,
          layout_style: ctx.layoutStyle,
          is_well_known: ctx.isWellKnown,
          author: ctx.authorName || undefined,
          well_known_book_title: ctx.wellKnownBookTitle || undefined,
          similar_book_title: ctx.similarBookTitle || undefined,
          scene_count: ctx.sceneCount,
        },
        {
          onProgress: (currentChunk, totalChunks) =>
            setAnalysisProgress({ currentChunk, totalChunks }),
        },
      );

      // Navigate to analysis review so user can select main entities
      navigate(`/books/${ctx.book.id}/analysis-review`);
    } catch (err: unknown) {
      console.error(err);
      const detail =
        err && typeof err === 'object' && 'response' in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : undefined;
      alert(detail || 'Analysis failed. Please try again.');
      setStep('style');
    } finally {
      setAnalyzeLoading(false);
      setAnalysisProgress(null);
    }
  }

  return (
    <div className="min-h-screen bg-paper-cream flex items-center justify-center px-4 py-12">
      {step === 'upload' && <BookUpload onSuccess={handleUploadSuccess} />}
      {step === 'style' && (
        <StyleSelector onSubmit={handleAnalyze} loading={analyzeLoading} />
      )}
      {step === 'analyzing' && (
        <LoadingScreen
          mode="analysis"
          analysisProgress={analysisProgress}
          onCancel={() => {
            setStep('style');
            setAnalyzeLoading(false);
            setAnalysisProgress(null);
          }}
        />
      )}
    </div>
  );
}
