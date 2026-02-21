import { useState, useCallback } from 'react';
import { Upload, Loader2, AlertCircle, FileText, X, ChevronDown } from 'lucide-react';
import { api, type Book } from '../services/api';

export interface BookUploadMetadata {
  genre?: string;
  author?: string;
}

interface Props {
  onSuccess: (book: Book, metadata?: BookUploadMetadata) => void;
}

const GENRES = [
  'Children\'s',
  'Fantasy',
  'Science Fiction',
  'Romance',
  'Thriller',
  'Mystery',
  'Horror',
  'Historical Fiction',
  'Literary Fiction',
  'Young Adult',
  'Non-Fiction',
  'Other',
];

export default function BookUpload({ onSuccess }: Props) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  
  // Form fields
  const [title, setTitle] = useState('');
  const [author, setAuthor] = useState('');
  const [genre, setGenre] = useState('Fantasy');
  const [pageCount, setPageCount] = useState('');

  const MAX_SIZE = 20 * 1024 * 1024; // 20MB
  const ACCEPTED_TYPES = ['.txt', '.docx', '.pdf'];

  const validateFile = (file: File): string | null => {
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!ACCEPTED_TYPES.includes(ext)) {
      return `Invalid file type. Please upload ${ACCEPTED_TYPES.join(', ')} files only.`;
    }
    if (file.size > MAX_SIZE) {
      return `File too large (${(file.size / (1024 * 1024)).toFixed(1)}MB). Maximum size is 20MB.`;
    }
    return null;
  };

  const handleFileSelect = useCallback((file: File) => {
    const validationError = validateFile(file);
    if (validationError) {
      setError(validationError);
      return;
    }

    setSelectedFile(file);
    setError(null);
    
    // Pre-fill title from filename
    const filenameWithoutExt = file.name.replace(/\.[^/.]+$/, '');
    const cleanTitle = filenameWithoutExt.replace(/[-_]/g, ' ');
    setTitle(cleanTitle);
    
    // Estimate page count from file size (rough estimate: 2KB per page)
    const estimatedPages = Math.max(1, Math.round(file.size / 2048));
    setPageCount(estimatedPages.toString());
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const file = e.dataTransfer.files[0];
    if (file) {
      handleFileSelect(file);
    }
  }, [handleFileSelect]);

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  const handleRemoveFile = () => {
    setSelectedFile(null);
    setTitle('');
    setPageCount('');
    setError(null);
  };

  const handleUpload = async () => {
    if (!selectedFile || !author.trim()) return;

    setLoading(true);
    setError(null);
    setUploadProgress(0);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      const response = await api.post<Book>(
        '/manuscripts/upload',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          timeout: 300_000, // 5 min – upload + backend processing can be slow
          onUploadProgress: (progressEvent) => {
            if (progressEvent.total) {
              const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
              setUploadProgress(percent);
            } else if (selectedFile?.size && progressEvent.loaded != null) {
              const percent = Math.min(99, Math.round((progressEvent.loaded * 100) / selectedFile.size));
              setUploadProgress(percent);
            }
          },
        }
      );

      const book = response.data;

      // Automatically chunk the uploaded book (can be slow for long manuscripts)
      await api.post(`/books/${book.id}/chunk`, {}, {
        timeout: 300_000, // 5 min
      });

      onSuccess(book, { genre, author: author.trim() || undefined });
    } catch (err: unknown) {
      const detail =
        err &&
        typeof err === 'object' &&
        'response' in err &&
        err.response &&
        typeof (err.response as { data?: { detail?: string } }).data === 'object'
          ? (err.response as { data: { detail?: string } }).data?.detail
          : undefined;
      const msg = typeof detail === 'string'
        ? detail
        : err instanceof Error
          ? err.message
          : 'Upload failed. Please try again.';
      setError(msg);
    } finally {
      setLoading(false);
      setUploadProgress(0);
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const isFormValid = selectedFile && author.trim().length > 0;

  return (
    <div className="w-full max-w-2xl space-y-6">
      <div className="space-y-2 text-center">
        <h2 className="font-display text-3xl font-semibold text-charcoal">
          Upload Your Manuscript
        </h2>
        <p className="text-sepia font-body text-sm">
          Upload your book file to get started with AI-powered cover generation
        </p>
      </div>

      {/* Drag-and-drop zone */}
      {!selectedFile && (
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`relative border-2 border-dashed rounded-xl p-12 text-center transition-all cursor-pointer ${
            isDragging
              ? 'border-golden bg-golden/5'
              : 'border-sepia/30 hover:border-golden/50 hover:bg-white/50'
          }`}
          onClick={() => document.getElementById('file-input')?.click()}
        >
          <input
            id="file-input"
            type="file"
            accept={ACCEPTED_TYPES.join(',')}
            onChange={handleFileInputChange}
            className="hidden"
          />
          
          <div className="space-y-4">
            <div className="flex justify-center">
              <div className="p-4 rounded-full bg-golden/10">
                <Upload size={32} className="text-golden" />
              </div>
            </div>
            
            <div className="space-y-1">
              <p className="font-ui text-base text-charcoal font-medium">
                Drop your manuscript here or click to browse
              </p>
              <p className="font-ui text-sm text-sepia">
                Supports .txt, .docx, .pdf (max 20MB)
              </p>
            </div>
          </div>
        </div>
      )}

      {/* File preview card */}
      {selectedFile && !loading && (
        <div className="p-4 rounded-xl bg-white/70 border border-sepia/20 space-y-4">
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-lg bg-golden/10 flex-shrink-0">
              <FileText size={24} className="text-golden" />
            </div>
            
            <div className="flex-1 min-w-0">
              <p className="font-ui text-sm font-semibold text-charcoal truncate">
                {selectedFile.name}
              </p>
              <p className="font-ui text-xs text-sepia">
                {formatFileSize(selectedFile.size)}
              </p>
            </div>
            
            <button
              onClick={handleRemoveFile}
              className="p-1.5 rounded-lg hover:bg-red-50 text-sepia hover:text-red-500 transition-colors"
              title="Remove file"
            >
              <X size={18} />
            </button>
          </div>

          {/* Metadata form */}
          <div className="pt-2 space-y-3">
            <div className="space-y-1.5">
              <label className="block font-ui text-xs font-medium text-charcoal">
                Book Title <span className="text-dusty-rose">*</span>
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Enter book title"
                className="w-full px-3 py-2 rounded-lg border border-sepia/30 bg-white
                           font-ui text-sm text-charcoal placeholder:text-sepia/50
                           focus:outline-none focus:ring-2 focus:ring-golden/50 focus:border-golden
                           transition-colors"
              />
            </div>

            <div className="space-y-1.5">
              <label className="block font-ui text-xs font-medium text-charcoal">
                Author Name <span className="text-dusty-rose">*</span>
              </label>
              <input
                type="text"
                value={author}
                onChange={(e) => setAuthor(e.target.value)}
                placeholder="Your name"
                className="w-full px-3 py-2 rounded-lg border border-sepia/30 bg-white
                           font-ui text-sm text-charcoal placeholder:text-sepia/50
                           focus:outline-none focus:ring-2 focus:ring-golden/50 focus:border-golden
                           transition-colors"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <label className="block font-ui text-xs font-medium text-charcoal">
                  Genre
                </label>
                <div className="relative">
                  <select
                    value={genre}
                    onChange={(e) => setGenre(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-sepia/30 bg-white
                               font-ui text-sm text-charcoal appearance-none cursor-pointer
                               focus:outline-none focus:ring-2 focus:ring-golden/50 focus:border-golden
                               transition-colors"
                  >
                    {GENRES.map((g) => (
                      <option key={g} value={g}>
                        {g}
                      </option>
                    ))}
                  </select>
                  <ChevronDown
                    size={16}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-sepia pointer-events-none"
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="block font-ui text-xs font-medium text-charcoal">
                  Page Count (est.)
                </label>
                <input
                  type="number"
                  value={pageCount}
                  onChange={(e) => setPageCount(e.target.value)}
                  placeholder="250"
                  min="1"
                  className="w-full px-3 py-2 rounded-lg border border-sepia/30 bg-white
                             font-ui text-sm text-charcoal placeholder:text-sepia/50
                             focus:outline-none focus:ring-2 focus:ring-golden/50 focus:border-golden
                             transition-colors"
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Upload progress */}
      {loading && (
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm font-ui text-charcoal">
            <span>Uploading manuscript...</span>
            <span>{uploadProgress}%</span>
          </div>
          <div className="h-2 bg-sepia/10 rounded-full overflow-hidden">
            <div
              className="h-full bg-golden transition-all duration-300"
              style={{ width: `${uploadProgress}%` }}
            />
          </div>
        </div>
      )}

      {/* Error message */}
      {error && (
        <div className="flex items-start gap-2 p-3 rounded-lg bg-dusty-rose/10 border border-dusty-rose/30">
          <AlertCircle size={16} className="text-dusty-rose mt-0.5 shrink-0" />
          <p className="text-dusty-rose text-sm font-ui">{error}</p>
        </div>
      )}

      {/* Upload button */}
      <button
        onClick={handleUpload}
        disabled={!isFormValid || loading}
        className="w-full flex items-center justify-center gap-2 px-6 py-3 rounded-lg
                   font-ui font-semibold text-paper-cream
                   bg-midnight hover:bg-midnight/90
                   disabled:opacity-40 disabled:cursor-not-allowed
                   transition-colors shadow cursor-pointer"
      >
        {loading ? (
          <>
            <Loader2 size={18} className="animate-spin" />
            Uploading... {uploadProgress}%
          </>
        ) : (
          <>
            <Upload size={18} />
            Upload & Continue
          </>
        )}
      </button>

      <p className="text-center text-xs text-sepia font-ui">
        By uploading, you agree that you own the rights to this manuscript
      </p>
    </div>
  );
}
