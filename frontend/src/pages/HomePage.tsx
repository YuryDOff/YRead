import { useNavigate } from 'react-router-dom';
import { BookOpen, Sparkles, Image } from 'lucide-react';

export default function HomePage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4 bg-paper-cream">
      {/* Hero */}
      <div className="max-w-2xl text-center space-y-8">
        <h1 className="font-display text-5xl md:text-6xl font-bold text-charcoal leading-tight">
          Reading<br />
          <span className="text-golden">Reinvented</span>
        </h1>

        <p className="font-body text-lg text-sepia max-w-lg mx-auto leading-relaxed">
          Transform any book into an immersive visual journey with AI-generated illustrations
          that bring every scene to life.
        </p>

        {/* Feature pills */}
        <div className="flex flex-wrap justify-center gap-4 pt-2">
          {[
            { icon: BookOpen, label: 'Import any book' },
            { icon: Sparkles, label: 'AI-powered analysis' },
            { icon: Image, label: 'Custom illustrations' },
          ].map(({ icon: Icon, label }) => (
            <div
              key={label}
              className="flex items-center gap-2 px-4 py-2 rounded-full
                         bg-white/60 border border-sepia/20 text-charcoal text-sm font-ui"
            >
              <Icon size={16} className="text-golden" />
              {label}
            </div>
          ))}
        </div>

        {/* CTA */}
        <button
          onClick={() => navigate('/setup')}
          className="mt-4 px-8 py-3.5 rounded-lg font-ui font-semibold text-paper-cream
                     bg-midnight hover:bg-midnight/90 transition-colors shadow-md
                     hover:shadow-lg cursor-pointer"
        >
          Start Reading
        </button>
      </div>
    </div>
  );
}
