import { useState, useEffect } from 'react';
import { Loader2, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const ANALYSIS_MESSAGES = [
  'Analyzing narrative structure...',
  'Identifying key characters...',
  'Mapping dramatic moments...',
  'Extracting locations...',
];

const GENERATION_MESSAGES = [
  'Generating your personalized illustrated book...',
  'Creating illustrations...',
  'Bringing your book to life...',
  'Applying artistic style...',
  'Almost there...',
];

interface Props {
  mode: 'analysis' | 'generation';
  /** When set (analysis mode), shows chunk progress bar. */
  analysisProgress?: { currentChunk: number; totalChunks: number } | null;
  onCancel?: () => void;
}

export default function LoadingScreen({ mode, analysisProgress, onCancel }: Props) {
  const messages = mode === 'analysis' ? ANALYSIS_MESSAGES : GENERATION_MESSAGES;
  const [msgIdx, setMsgIdx] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setMsgIdx((prev) => (prev + 1) % messages.length);
    }, 4000);
    return () => clearInterval(interval);
  }, [messages.length]);

  return (
    <div className="min-h-[60vh] flex flex-col items-center justify-center gap-8 px-4">
      {/* Animated spinner ring */}
      <div className="relative w-20 h-20">
        <div className="absolute inset-0 rounded-full border-4 border-sepia/15" />
        <div className="absolute inset-0 rounded-full border-4 border-t-golden border-r-transparent border-b-transparent border-l-transparent animate-spin" />
        <Loader2
          size={28}
          className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-golden animate-pulse"
        />
      </div>

      {/* Rotating message */}
      <div className="h-8 overflow-hidden">
        <AnimatePresence mode="wait">
          <motion.p
            key={msgIdx}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -12 }}
            transition={{ duration: 0.35 }}
            className="font-body text-base text-charcoal text-center"
          >
            {messages[msgIdx]}
          </motion.p>
        </AnimatePresence>
      </div>

      {/* Progress (analysis only): show indeterminate until we have chunk counts */}
      {mode === 'analysis' && (
        <div className="w-full max-w-xs space-y-1">
          {analysisProgress && analysisProgress.totalChunks > 0 ? (
            <>
              <div className="h-2 w-full rounded-full bg-sepia/15 overflow-hidden">
                <motion.div
                  className="h-full rounded-full bg-golden"
                  initial={{ width: 0 }}
                  animate={{
                    width: `${Math.min(
                      100,
                      (100 * analysisProgress.currentChunk) / analysisProgress.totalChunks,
                    )}%`,
                  }}
                  transition={{ duration: 0.4 }}
                />
              </div>
              <p className="font-ui text-xs text-sepia text-center">
                Chunk {analysisProgress.currentChunk} of {analysisProgress.totalChunks}
              </p>
            </>
          ) : (
            <>
              <div className="h-2 w-full rounded-full bg-sepia/15 overflow-hidden">
                <motion.div
                  className="h-full rounded-full bg-golden/70"
                  animate={{ width: ['20%', '60%', '20%'] }}
                  transition={{
                    duration: 2,
                    repeat: Infinity,
                    repeatType: 'reverse',
                  }}
                />
              </div>
              <p className="font-ui text-xs text-sepia text-center">
                Preparing analysis…
              </p>
            </>
          )}
        </div>
      )}

      <p className="font-ui text-xs text-sepia">
        {mode === 'analysis'
          ? 'This can take 3–15 minutes for long books. Do not close the tab.'
          : 'Generating your first illustrations...'}
      </p>

      {/* Cancel */}
      {onCancel && (
        <button
          onClick={onCancel}
          className="flex items-center gap-1.5 px-4 py-2 rounded-lg
                     font-ui text-sm text-sepia hover:text-charcoal
                     border border-sepia/20 hover:border-sepia/40
                     transition-colors cursor-pointer"
        >
          <X size={14} />
          Cancel
        </button>
      )}
    </div>
  );
}
