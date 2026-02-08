import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useBook } from '../context/BookContext';
import BookUpload from '../components/BookUpload';
import StyleSelector from '../components/StyleSelector';
import LoadingScreen from '../components/LoadingScreen';
import { analyzeBook, searchReferences, type Book } from '../services/api';

type Step = 'upload' | 'style' | 'analyzing';

export default function SetupPage() {
  const navigate = useNavigate();
  const ctx = useBook();
  const [step, setStep] = useState<Step>(ctx.book ? 'style' : 'upload');
  const [analyzeLoading, setAnalyzeLoading] = useState(false);

  function handleUploadSuccess(book: Book) {
    ctx.setBook(book);
    setStep('style');
  }

  async function handleAnalyze() {
    if (!ctx.book) return;
    setAnalyzeLoading(true);
    setStep('analyzing');
    try {
      await analyzeBook(ctx.book.id, {
        style_category: ctx.styleCategory,
        illustration_frequency: ctx.illustrationFrequency,
        layout_style: ctx.layoutStyle,
        is_well_known: ctx.isWellKnown,
        author: ctx.authorName || undefined,
      });

      // Search reference images
      const refs = await searchReferences(ctx.book.id);
      ctx.setReferenceImages(refs);

      navigate('/visual-bible');
    } catch (err) {
      console.error(err);
      // Go back to style selector on error
      setStep('style');
    } finally {
      setAnalyzeLoading(false);
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
          onCancel={() => {
            setStep('style');
            setAnalyzeLoading(false);
          }}
        />
      )}
    </div>
  );
}
