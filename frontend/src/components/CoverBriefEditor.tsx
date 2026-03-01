import { useState } from 'react';

export default function CoverBriefEditor({
  initialInstruction = '',
  onSubmit,
}: {
  initialInstruction?: string;
  onSubmit?: (instruction: string) => void;
}) {
  const [instruction, setInstruction] = useState(initialInstruction);

  return (
    <section className="rounded border p-4 bg-white space-y-2">
      <h3 className="font-semibold">Cover Brief Editor</h3>
      <textarea
        className="w-full border rounded p-2 min-h-24"
        value={instruction}
        onChange={(e) => setInstruction(e.target.value)}
        placeholder="Describe desired cover direction..."
      />
      <button className="px-3 py-2 rounded bg-black text-white" onClick={() => onSubmit?.(instruction)}>
        Save Brief
      </button>
    </section>
  );
}
