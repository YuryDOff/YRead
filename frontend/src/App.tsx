import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { BookProvider } from './context/BookContext';
import HomePage from './pages/HomePage';
import SetupPage from './pages/SetupPage';
import VisualBiblePage from './pages/VisualBiblePage';
import ReadingPage from './pages/ReadingPage';

export default function App() {
  return (
    <BookProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/setup" element={<SetupPage />} />
          <Route path="/visual-bible" element={<VisualBiblePage />} />
          <Route path="/read" element={<ReadingPage />} />
        </Routes>
      </BrowserRouter>
    </BookProvider>
  );
}
