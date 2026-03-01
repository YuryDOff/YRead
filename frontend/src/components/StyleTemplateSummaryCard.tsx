export default function StyleTemplateSummaryCard({ template }: { template: string }) {
  return (
    <div className="rounded border p-4 bg-white">
      <h3 className="font-semibold mb-1">Reference Style Template</h3>
      <p className="text-sm text-gray-700">{template || 'No analyzed reference yet.'}</p>
    </div>
  );
}
