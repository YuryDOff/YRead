import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { generateCoverConcepts, listCoverConcepts, type CoverConcept } from '../services/api';

export default function CoverStudioPage() {
  const { bookId } = useParams<{ bookId: string }>();
  const [concepts, setConcepts] = useState<CoverConcept[]>([]);
  const id = Number(bookId);

  async function refresh() {
    if (!id) return;
    setConcepts(await listCoverConcepts(id));
  }

  useEffect(() => {
    void refresh();
  }, [id]);

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-2xl font-semibold">Cover Studio</h1>
      <button
        className="px-3 py-2 rounded bg-black text-white"
        onClick={async () => {
          await generateCoverConcepts(id, { concept_count: 3 });
          await refresh();
        }}
      >
        Generate Concepts
      </button>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {concepts.map((c) => (
          <div key={c.id} className="border rounded p-3">
            <p className="font-medium">Concept {c.concept_index}</p>
            <p className="text-xs text-gray-600">{c.status}</p>
            {c.image_path ? <img src={c.image_path} alt={`Concept ${c.concept_index}`} className="mt-2 rounded" /> : null}
          </div>
        ))}
      </div>
    </div>
  );
}
