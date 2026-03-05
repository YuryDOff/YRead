import { useEffect, useRef, useState } from 'react';
import { useParams } from 'react-router-dom';
import { FeatureGate } from '../components/FeatureGate';
import { useBook } from '../context/BookContext';

const KDP_EXPORT_SPEC = 'Export: 2560×1600px · 300dpi · 0.125" bleed · KDP compatible';
const EXPORT_WIDTH = 2560;
const EXPORT_HEIGHT = 1600;

const GENRE_FONTS: Record<string, { title: string; author: string }> = {
  fantasy: { title: 'Cinzel', author: 'Lora' },
  romance: { title: 'Playfair Display', author: 'Crimson Text' },
  thriller: { title: 'Oswald', author: 'Open Sans' },
  default: { title: 'Playfair Display', author: 'Lora' },
};

export default function TextStudioPage() {
  const { bookId } = useParams<{ bookId: string }>();
  const ctx = useBook();
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [title, setTitle] = useState('');
  const [author, setAuthor] = useState('');
  const [titleFont, setTitleFont] = useState('Playfair Display');
  const [authorFont, setAuthorFont] = useState('Lora');
  const [textColor, setTextColor] = useState('#1a1a1a');
  const [titleSize, setTitleSize] = useState(72);
  const [authorSize, setAuthorSize] = useState(36);
  const [coverImageUrl, setCoverImageUrl] = useState<string | null>(null);
  const [titlePos, setTitlePos] = useState({ x: 0.5, y: 0.15 });
  const [authorPos, setAuthorPos] = useState({ x: 0.5, y: 0.88 });

  const id = bookId ? Number(bookId) : null;

  useEffect(() => {
    if (typeof localStorage !== 'undefined') {
      const url = localStorage.getItem('noctua_selected_cover_url');
      if (url) setCoverImageUrl(url);
    }
    if (ctx.book?.title) setTitle(ctx.book.title);
    if (ctx.book?.author) setAuthor(ctx.book.author || '');
  }, [ctx.book?.title, ctx.book?.author]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx2d = canvas.getContext('2d');
    if (!ctx2d) return;

    const img = new Image();
    img.crossOrigin = 'anonymous';
    const src = coverImageUrl
      ? (coverImageUrl.startsWith('http') ? coverImageUrl : `${window.location.origin}${coverImageUrl}`)
      : '';
    if (!src) {
      ctx2d.fillStyle = '#2c2c2c';
      ctx2d.fillRect(0, 0, canvas.width, canvas.height);
      ctx2d.fillStyle = '#888';
      ctx2d.font = '24px sans-serif';
      ctx2d.textAlign = 'center';
      ctx2d.fillText('Select a cover concept in Cover Studio', canvas.width / 2, canvas.height / 2);
      return;
    }
    img.onload = () => {
      ctx2d.clearRect(0, 0, canvas.width, canvas.height);
      ctx2d.drawImage(img, 0, 0, canvas.width, canvas.height);
      ctx2d.fillStyle = textColor;
      ctx2d.textAlign = 'center';
      ctx2d.textBaseline = 'middle';
      ctx2d.font = `${titleSize}px "${titleFont}", serif`;
      ctx2d.fillText(title || 'Title', canvas.width * titlePos.x, canvas.height * titlePos.y);
      ctx2d.font = `${authorSize}px "${authorFont}", serif`;
      ctx2d.fillText(author || 'Author', canvas.width * authorPos.x, canvas.height * authorPos.y);
    };
    img.onerror = () => {
      ctx2d.fillStyle = '#2c2c2c';
      ctx2d.fillRect(0, 0, canvas.width, canvas.height);
    };
    img.src = src;
  }, [coverImageUrl, title, author, titleFont, authorFont, textColor, titleSize, authorSize, titlePos, authorPos]);

  function handleExport() {
    const canvas = document.createElement('canvas');
    canvas.width = EXPORT_WIDTH;
    canvas.height = EXPORT_HEIGHT;
    const ctx2d = canvas.getContext('2d');
    if (!ctx2d) return;
    const img = new Image();
    img.crossOrigin = 'anonymous';
    const src = coverImageUrl
      ? (coverImageUrl.startsWith('http') ? coverImageUrl : `${window.location.origin}${coverImageUrl}`)
      : '';
    if (!src) return;
    img.onload = () => {
      ctx2d.drawImage(img, 0, 0, EXPORT_WIDTH, EXPORT_HEIGHT);
      ctx2d.fillStyle = textColor;
      ctx2d.textAlign = 'center';
      ctx2d.textBaseline = 'middle';
      ctx2d.font = `${Math.round((titleSize * EXPORT_WIDTH) / 800)}px "${titleFont}", serif`;
      ctx2d.fillText(title || 'Title', EXPORT_WIDTH * titlePos.x, EXPORT_HEIGHT * titlePos.y);
      ctx2d.font = `${Math.round((authorSize * EXPORT_WIDTH) / 800)}px "${authorFont}", serif`;
      ctx2d.fillText(author || 'Author', EXPORT_WIDTH * authorPos.x, EXPORT_HEIGHT * authorPos.y);
      canvas.toBlob((blob) => {
        if (!blob) return;
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = `noctua-cover-${(title || 'cover').replace(/\s+/g, '-')}.png`;
        a.click();
        URL.revokeObjectURL(a.href);
      }, 'image/png');
    };
    img.src = src;
  }

  if (!id) {
    return (
      <div className="min-h-screen bg-paper-cream flex items-center justify-center px-4">
        <p className="font-ui text-sepia">Invalid book.</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-paper-cream p-6 flex flex-col lg:flex-row gap-6 max-w-6xl mx-auto">
      <div className="flex-1">
        <h1 className="font-display text-2xl text-ink-black mb-4">Typography</h1>
        <div className="rounded border border-sepia/30 bg-charcoal/5 overflow-hidden">
          <canvas
            ref={canvasRef}
            width={800}
            height={1200}
            className="w-full max-w-full h-auto block"
            style={{ aspectRatio: '2/3' }}
          />
        </div>
      </div>
      <aside className="w-full lg:w-72 space-y-4">
        <div>
          <label className="block font-ui text-sm text-charcoal mb-1">Title</label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full px-3 py-2 rounded border border-sepia/20 font-ui text-sm"
          />
        </div>
        <div>
          <label className="block font-ui text-sm text-charcoal mb-1">Title font</label>
          <select
            value={titleFont}
            onChange={(e) => setTitleFont(e.target.value)}
            className="w-full px-3 py-2 rounded border border-sepia/20 font-ui text-sm"
          >
            {Object.entries(GENRE_FONTS).map(([k, v]) => (
              <option key={k} value={v.title}>{v.title}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block font-ui text-sm text-charcoal mb-1">Author</label>
          <input
            type="text"
            value={author}
            onChange={(e) => setAuthor(e.target.value)}
            className="w-full px-3 py-2 rounded border border-sepia/20 font-ui text-sm"
          />
        </div>
        <div>
          <label className="block font-ui text-sm text-charcoal mb-1">Author font</label>
          <select
            value={authorFont}
            onChange={(e) => setAuthorFont(e.target.value)}
            className="w-full px-3 py-2 rounded border border-sepia/20 font-ui text-sm"
          >
            {Object.entries(GENRE_FONTS).map(([k, v]) => (
              <option key={k} value={v.author}>{v.author}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block font-ui text-sm text-charcoal mb-1">Text color</label>
          <input
            type="color"
            value={textColor}
            onChange={(e) => setTextColor(e.target.value)}
            className="w-full h-10 rounded border border-sepia/20"
          />
        </div>
        <div>
          <label className="block font-ui text-sm text-charcoal mb-1">Title size</label>
          <input
            type="range"
            min={24}
            max={120}
            value={titleSize}
            onChange={(e) => setTitleSize(Number(e.target.value))}
            className="w-full"
          />
          <span className="text-xs text-sepia">{titleSize}px</span>
        </div>
        <FeatureGate fallback={null} plan="pro">
          <div>
            <label className="block font-ui text-sm text-charcoal mb-1">Upload custom font</label>
            <p className="text-xs text-sepia">Pro: upload your own font file (placeholder).</p>
          </div>
        </FeatureGate>
        <p className="text-xs text-sepia">{KDP_EXPORT_SPEC}</p>
        <button
          type="button"
          onClick={handleExport}
          className="w-full px-4 py-2 rounded bg-midnight text-white font-ui"
        >
          Export PNG (KDP compatible)
        </button>
      </aside>
    </div>
  );
}
