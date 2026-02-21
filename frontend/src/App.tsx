import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthorWorkflowProvider } from './context/BookContext';
import WorkflowLayout from './components/WorkflowLayout';
import HomePage from './pages/HomePage';
import CreateBookPage from './pages/SetupPage';
import AnalysisReviewPage from './pages/AnalysisReviewPage';
import ReviewSearchPage from './pages/ReviewSearchPage';
import ReviewSearchResultPage from './pages/ReviewSearchResultPage';
import VisualBiblePage from './pages/VisualBiblePage';
import PreviewPage from './pages/ReadingPage';
import SettingsPage from './pages/SettingsPage';

export default function App() {
  return (
    <AuthorWorkflowProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/settings" element={<SettingsPage />} />
          {/* New book flow: no bookId in URL */}
          <Route path="/manuscript-upload" element={<WorkflowLayout />}>
            <Route index element={<CreateBookPage />} />
          </Route>
          {/* Existing book: bookId in URL so refresh keeps position */}
          <Route path="/books/:bookId" element={<WorkflowLayout />}>
            <Route index element={<Navigate to="preview" replace />} />
            <Route path="manuscript-upload" element={<CreateBookPage />} />
            <Route path="analysis-review" element={<AnalysisReviewPage />} />
            <Route path="review-search" element={<ReviewSearchPage />} />
            <Route path="review-search-result" element={<ReviewSearchResultPage />} />
            <Route path="visual-bible" element={<VisualBiblePage />} />
            <Route path="preview" element={<PreviewPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthorWorkflowProvider>
  );
}
