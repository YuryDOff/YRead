import { useState } from "react";

const COLORS = {
  built: "#2d6a4f",
  builtBg: "#d8f3dc",
  builtBorder: "#52b788",
  new: "#7b2d8b",
  newBg: "#f3d8fc",
  newBorder: "#c77dff",
  pivot: "#b5450b",
  pivotBg: "#fde8d8",
  pivotBorder: "#f4a261",
  data: "#1a4a7a",
  dataBg: "#d8eaf8",
  dataBorder: "#4a9eda",
  user: "#555",
  userBg: "#f5f5f5",
  userBorder: "#aaa",
};

const Legend = () => (
  <div style={{ display: "flex", gap: 24, flexWrap: "wrap", marginBottom: 28, padding: "12px 16px", background: "#fafafa", borderRadius: 8, border: "1px solid #e0e0e0" }}>
    {[
      { color: COLORS.builtBg, border: COLORS.builtBorder, label: "Built (Phases 1–7)" },
      { color: COLORS.pivotBg, border: COLORS.pivotBorder, label: "Pivot / Enhance existing" },
      { color: COLORS.newBg, border: COLORS.newBorder, label: "New module" },
      { color: COLORS.dataBg, border: COLORS.dataBorder, label: "Data store" },
      { color: COLORS.userBg, border: COLORS.userBorder, label: "User action" },
    ].map(({ color, border, label }) => (
      <div key={label} style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <div style={{ width: 20, height: 20, background: color, border: `2px solid ${border}`, borderRadius: 4 }} />
        <span style={{ fontSize: 13, color: "#444" }}>{label}</span>
      </div>
    ))}
  </div>
);

const Box = ({ label, sublabel, type = "built", width = 160, onClick, active }) => {
  const c = {
    built: { bg: COLORS.builtBg, border: COLORS.builtBorder, text: COLORS.built },
    new: { bg: COLORS.newBg, border: COLORS.newBorder, text: COLORS.new },
    pivot: { bg: COLORS.pivotBg, border: COLORS.pivotBorder, text: COLORS.pivot },
    data: { bg: COLORS.dataBg, border: COLORS.dataBorder, text: COLORS.data },
    user: { bg: COLORS.userBg, border: COLORS.userBorder, text: COLORS.user },
  }[type];

  return (
    <div
      onClick={onClick}
      style={{
        width,
        minHeight: 52,
        background: c.bg,
        border: `2px solid ${active ? "#222" : c.border}`,
        borderRadius: 8,
        padding: "8px 10px",
        cursor: onClick ? "pointer" : "default",
        boxShadow: active ? "0 0 0 3px #222a" : "none",
        transition: "box-shadow 0.15s",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        textAlign: "center",
        userSelect: "none",
      }}
    >
      <div style={{ fontSize: 12, fontWeight: 700, color: c.text, lineHeight: 1.3 }}>{label}</div>
      {sublabel && <div style={{ fontSize: 10, color: "#666", marginTop: 3, lineHeight: 1.2 }}>{sublabel}</div>}
    </div>
  );
};

const Arrow = ({ label, color = "#888", vertical = false }) => (
  <div style={{ display: "flex", alignItems: "center", justifyContent: "center", flexDirection: vertical ? "column" : "row", flexShrink: 0 }}>
    {label && <span style={{ fontSize: 10, color, marginBottom: vertical ? 2 : 0, marginRight: vertical ? 0 : 4, whiteSpace: "nowrap" }}>{label}</span>}
    <div style={{
      width: vertical ? 2 : 32,
      height: vertical ? 24 : 2,
      background: color,
      position: "relative",
    }}>
      <div style={{
        position: "absolute",
        ...(vertical
          ? { bottom: -5, left: "50%", transform: "translateX(-50%)", borderLeft: "5px solid transparent", borderRight: "5px solid transparent", borderTop: `7px solid ${color}` }
          : { right: -5, top: "50%", transform: "translateY(-50%)", borderTop: "5px solid transparent", borderBottom: "5px solid transparent", borderLeft: `7px solid ${color}` })
      }} />
    </div>
  </div>
);

const SectionHeader = ({ children }) => (
  <div style={{ fontSize: 11, fontWeight: 700, color: "#888", textTransform: "uppercase", letterSpacing: 1, marginBottom: 10 }}>{children}</div>
);

const InfoPanel = ({ node, onClose }) => {
  if (!node) return null;
  return (
    <div style={{
      position: "fixed", top: 80, right: 24, width: 320, background: "#fff",
      border: "1.5px solid #ccc", borderRadius: 12, padding: 20, zIndex: 100,
      boxShadow: "0 8px 32px #0002"
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
        <div style={{ fontWeight: 700, fontSize: 14 }}>{node.label}</div>
        <button onClick={onClose} style={{ background: "none", border: "none", fontSize: 18, cursor: "pointer", color: "#888" }}>×</button>
      </div>
      <div style={{ fontSize: 12, color: "#444", lineHeight: 1.6 }}>{node.detail}</div>
      {node.inputs && (
        <div style={{ marginTop: 12 }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: "#888", textTransform: "uppercase", marginBottom: 4 }}>Inputs</div>
          {node.inputs.map(i => <div key={i} style={{ fontSize: 11, color: "#2d6a4f", marginBottom: 2 }}>← {i}</div>)}
        </div>
      )}
      {node.outputs && (
        <div style={{ marginTop: 8 }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: "#888", textTransform: "uppercase", marginBottom: 4 }}>Outputs</div>
          {node.outputs.map(o => <div key={o} style={{ fontSize: 11, color: "#7b2d8b", marginBottom: 2 }}>→ {o}</div>)}
        </div>
      )}
      {node.status && (
        <div style={{ marginTop: 12, padding: "6px 10px", background: node.type === "built" ? COLORS.builtBg : node.type === "new" ? COLORS.newBg : COLORS.pivotBg, borderRadius: 6, fontSize: 11, fontWeight: 600, color: node.type === "built" ? COLORS.built : node.type === "new" ? COLORS.new : COLORS.pivot }}>
          {node.status}
        </div>
      )}
    </div>
  );
};

const NODES = {
  upload: {
    label: "Manuscript Upload",
    type: "built",
    status: "✅ Built — Phase 1",
    detail: "User uploads .txt, .docx, or .pdf. Validated, chunked into ~2000-token overlapping chunks. Book record created with title, genre, word count.",
    inputs: ["User file (.txt / .docx / .pdf)", "Genre, title, author"],
    outputs: ["Chunks stored in DB", "Book metadata"],
  },
  analysis: {
    label: "AI Analysis Engine",
    sublabel: "Characters · Locations · Artefacts · Cover",
    type: "built",
    status: "✅ Built — Phases 1–6",
    detail: "Multi-entity analysis pipeline. Runs batch chunk analysis via GPT-4o-mini, then consolidates into main characters, locations, artefacts. Assigns ontology classes, visual tokens, and cover brief. Each entity type runs independently with progress tracking.",
    inputs: ["Chunks", "Genre", "Entity types to analyse"],
    outputs: ["Characters + visual tokens", "Locations + visual tokens", "Artefacts + visual tokens", "Cover analysis + mood/palette/type", "Scenes with dramatic scores"],
  },
  entityDB: {
    label: "Entity Database",
    sublabel: "Characters · Locations · Artefacts · Scenes",
    type: "data",
    status: "✅ Built — Phases 1–6",
    detail: "PostgreSQL (SQLite in dev). Stores all extracted entities with ontology classifications, visual tokens, core/style/archetype/anti-token sets, selected_reference_urls, is_main flags.",
    inputs: ["Analysis pipeline output"],
    outputs: ["Entity queries for search, prompt assembly, T2I conditioning"],
  },
  analysisReview: {
    label: "Analysis Review UI",
    sublabel: "Select main entities",
    type: "built",
    status: "✅ Built — Phase 5 (partial gaps in Phase 7)",
    detail: "Four-tab UI: Characters / Locations / Artefacts / Cover. User reviews AI-extracted entities, marks is_main, reviews scenes and cover brief. Cover Brief Editor gap (Phase 7) shows cover type, primary element, colour palette.",
    inputs: ["Entity DB", "Cover analysis"],
    outputs: ["is_main selections", "Primary cover element", "Cover type confirmed"],
  },
  refSearch: {
    label: "Reference Search Engine",
    sublabel: "Unsplash · SerpAPI · Pexels · Pixabay · DeviantArt · Behance",
    type: "pivot",
    status: "✅ Built (Phase 6) — Pivot: add Serper provider",
    detail: "Multi-provider image search. Builds diversified queries per entity using visual tokens + ontology. Runs across enabled providers, deduplicates, ranks by aesthetic quality signals. Engine selector routes artefact/cover queries to art-heavy providers (Behance, DeviantArt). Serper to be added as new Google Images provider.",
    inputs: ["Entity visual tokens", "Proposed queries", "Engine ratings", "Enabled providers from settings"],
    outputs: ["Ranked reference images per entity", "provider_usage stats"],
  },
  serper: {
    label: "Serper Provider",
    sublabel: "Google Images via Serper.dev",
    type: "new",
    status: "🆕 New — test script first, then add to provider pool",
    detail: "Serper.dev wraps Google Search API including Google Images. Cheaper than SerpAPI (~$0.001/query vs ~$0.005). Supports image search with filtering. To be tested via standalone script, then integrated as a new provider following the existing base.py interface. Particularly useful for book cover searches and artefact reference images.",
    inputs: ["Search query string", "Serper API key"],
    outputs: ["Image results (url, thumbnail, width, height, credit)"],
  },
  moodboard: {
    label: "Moodboard & Reference Selector",
    sublabel: "Characters · Locations · Artefacts · Covers",
    type: "pivot",
    status: "✅ Built (ReviewSearchResultPage) — Pivot: add I2T trigger for cover references",
    detail: "User selects reference images per entity from search results. Can upload their own images. Approves Visual Bible selections. Cover tab now becomes the entry point for I2T pipeline — when a cover reference is selected or uploaded, it triggers the I2T analysis automatically.",
    inputs: ["Reference search results", "User-uploaded images"],
    outputs: ["selected_reference_urls per entity", "approved Visual Bible", "Cover reference images → I2T trigger"],
  },
  i2tService: {
    label: "I2T Analysis Service",
    sublabel: "GPT-4o Vision",
    type: "new",
    status: "🆕 New — core new module",
    detail: "Takes an image (book cover or illustration example) and calls GPT-4o Vision to extract a structured style description in T2I vocabulary. Returns: composition notes, lighting keywords, color palette, style tags, mood descriptors, rendering quality terms. Stores result as reference_style_template in cover_analysis or scene record. Cost: ~$0.0004/image (GPT-4o-mini) or ~$0.004 (GPT-4o full).",
    inputs: ["Reference image (cover or illustration)", "Extraction mode: cover | illustration"],
    outputs: ["style_template prompt string", "composition_notes", "color_palette_extracted", "style_tags[]"],
  },
  promptEngine: {
    label: "Prompt Engineering Service",
    sublabel: "Merge · Substitute · Validate",
    type: "new",
    status: "🆕 New — central intelligence module",
    detail: "The new heart of Noctua's generation pipeline. Takes an I2T-derived style template and merges it with entity-specific context from the database. Handles: (1) Cover mode — replace style template elements with character/location/artefact descriptions from the book. (2) Illustration mode — replace style template subject with scene description + entity visual tokens. Validates compositional compatibility before merge. If incompatibility detected, warns user or adapts composition. Replaces the deterministic CoverPromptAssembler for I2T-driven path; assembler becomes fallback.",
    inputs: ["I2T style_template", "Primary entity (character/location/artefact) from DB", "Scene description (illustration mode)", "User instruction (natural language substitution)"],
    outputs: ["Final merged T2I prompt", "Negative prompt", "Compatibility warnings"],
  },
  coverGeneration: {
    label: "Cover Generation",
    sublabel: "FLUX Kontext / DALL-E",
    type: "pivot",
    status: "🔧 Stub → implement in Phase 9 — pivot: I2T prompt replaces assembler as primary path",
    detail: "Calls FLUX Kontext (via fal.ai) or DALL-E. For I2T path: uses merged prompt from Prompt Engineering Service + optional Visual Bible entity reference images as image conditioning. For fallback path: uses CoverPromptAssembler deterministic prompt. Generates concept_count variants. Results stored as CoverConcept records.",
    inputs: ["Final merged prompt", "Negative prompt", "Visual Bible reference images (optional conditioning)", "Aspect ratio 2:3"],
    outputs: ["Generated cover image URL", "CoverConcept record with status"],
  },
  illustrationGeneration: {
    label: "Illustration Generation",
    sublabel: "FLUX / SD · Per scene",
    type: "new",
    status: "🆕 New — future module (post-cover launch)",
    detail: "Generates book illustrations per scene. Uses I2T-extracted style template (from user-uploaded illustration example) + scene description + character/location visual tokens. Reference images from Visual Bible used as conditioning for character consistency. This is Noctua's long-term vision: AI-illustrated reading experience.",
    inputs: ["Scene description + visual tokens", "I2T style_template (from illustration example)", "Character Visual Bible images (conditioning)", "Location Visual Bible images (conditioning)"],
    outputs: ["Illustration image per scene", "VisualBibleEntry record"],
  },
  typographyCompositor: {
    label: "Typography Compositor",
    sublabel: "TextStudio",
    type: "new",
    status: "🆕 New — Phase 13 (TextStudio)",
    detail: "Browser-side compositing. Renders generated cover image with title/author text overlay. User selects font (genre-appropriate curated library), size, position, color. Drag-to-reposition. Detects negative space zones in the generated image to suggest placement. Exports flattened PNG for download. No backend round-trip — pure canvas compositing.",
    inputs: ["Generated cover image", "Title text", "Author text", "Font selection", "Color/position choices"],
    outputs: ["Flattened cover PNG for download"],
  },
  visualBibleDB: {
    label: "Visual Bible",
    sublabel: "Approved reference images per entity",
    type: "data",
    status: "✅ Built — Phase 6",
    detail: "Stores approved reference image URLs per character, location, artefact, and cover. These flow into T2I generation as image conditioning references, giving FLUX Kontext visual anchors for consistent character/location rendering.",
    inputs: ["User selections from Moodboard"],
    outputs: ["selected_reference_urls → T2I conditioning", "Cover reference → I2T trigger"],
  },
  coverStudio: {
    label: "Cover Studio UI",
    sublabel: "Preview · Regenerate · Select",
    type: "new",
    status: "🆕 New — Phase 13",
    detail: "CoverStudio page. Shows generated cover concepts, allows user to select favourite, regenerate with tweaks, adjust prompt. Includes the Cover Brief Editor (primary element, cover type, assembled prompt preview). Feeds into TextStudio for typography.",
    inputs: ["CoverConcept records", "Cover Brief", "Assembled prompt preview"],
    outputs: ["Selected concept → TextStudio", "Regeneration requests"],
  },
};

export default function NoctuaArchitecture() {
  const [activeNode, setActiveNode] = useState(null);

  const handleClick = (key) => {
    setActiveNode(activeNode === key ? null : key);
  };

  const B = ({ k, width }) => (
    <Box
      label={NODES[k].label}
      sublabel={NODES[k].sublabel}
      type={NODES[k].type}
      width={width || 170}
      onClick={() => handleClick(k)}
      active={activeNode === k}
    />
  );

  const row = (children, style = {}) => (
    <div style={{ display: "flex", alignItems: "center", gap: 0, ...style }}>{children}</div>
  );

  const col = (children, style = {}) => (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 0, ...style }}>{children}</div>
  );

  const gap = (n = 8) => <div style={{ width: n, height: n, flexShrink: 0 }} />;

  return (
    <div style={{ fontFamily: "'Inter', 'Helvetica', sans-serif", padding: 24, background: "#f9f9f9", minHeight: "100vh" }}>
      <div style={{ maxWidth: 1100, margin: "0 auto" }}>

        <div style={{ marginBottom: 4 }}>
          <h1 style={{ fontSize: 22, fontWeight: 800, margin: 0, color: "#1a1a1a" }}>Noctua — Architecture & Data Flow</h1>
          <p style={{ color: "#666", fontSize: 13, marginTop: 4 }}>Click any module for details. Showing current state + proposed pivot.</p>
        </div>

        <Legend />

        {/* ── ROW 1: Ingestion ── */}
        <SectionHeader>1 · Ingestion & Analysis</SectionHeader>
        {row([
          col([
            <Box key="u" label="User uploads manuscript" type="user" width={150} />,
            <Arrow key="a" vertical />,
            <B key="up" k="upload" width={150} />,
          ]),
          <Arrow key="a1" label="chunks" />,
          <B key="an" k="analysis" width={200} />,
          <Arrow key="a2" label="entities" />,
          <B key="edb" k="entityDB" width={170} />,
        ], { marginBottom: 8 })}
        {gap(16)}

        {/* ── ROW 2: Review ── */}
        <SectionHeader>2 · Review & Entity Selection</SectionHeader>
        {row([
          <B key="ar" k="analysisReview" width={190} />,
          <Arrow key="a3" label="is_main flags" />,
          <B key="edb2" k="entityDB" width={170} />,
          gap(20),
          <div key="note" style={{ fontSize: 11, color: "#888", maxWidth: 220, lineHeight: 1.5, padding: "8px 12px", background: "#f0f0f0", borderRadius: 6 }}>
            Cover Brief Editor (Phase 7 gap): user confirms cover type, primary element, colour palette. These feed into Prompt Engineering Service.
          </div>
        ], { marginBottom: 8 })}
        {gap(16)}

        {/* ── ROW 3: Reference Search ── */}
        <SectionHeader>3 · Reference Image Search</SectionHeader>
        {row([
          col([
            <B key="rs" k="refSearch" width={230} />,
            <Arrow key="a4" vertical label="add provider" />,
            <B key="se" k="serper" width={230} />,
          ]),
          <Arrow key="a5" label="results" />,
          <B key="mb" k="moodboard" width={200} />,
          <Arrow key="a6" label="approved" />,
          <B key="vbdb" k="visualBibleDB" width={170} />,
        ], { marginBottom: 8 })}
        {gap(4)}
        {row([
          <div key="sp" style={{ width: 230 }} />,
          gap(32 + 14),
          <div key="note2" style={{ fontSize: 11, color: COLORS.pivot, fontWeight: 600, lineHeight: 1.5, padding: "6px 10px", background: COLORS.pivotBg, border: `1px solid ${COLORS.pivotBorder}`, borderRadius: 6, maxWidth: 200 }}>
            ↑ Pivot: cover tab in Moodboard triggers I2T automatically when image selected
          </div>
        ])}
        {gap(16)}

        {/* ── ROW 4: I2T + Prompt Engineering ── */}
        <SectionHeader>4 · I2T Analysis & Prompt Engineering  ← NEW CORE</SectionHeader>
        {row([
          col([
            <Box key="ui2t" label="User selects / uploads reference image" type="user" width={200} />,
            <Arrow key="a7" vertical />,
            <B key="i2t" k="i2tService" width={200} />,
          ]),
          <Arrow key="a8" label="style template" />,
          col([
            <B key="pe" k="promptEngine" width={200} />,
            <Arrow key="a9" vertical label="entity context" />,
            <B key="edb3" k="entityDB" width={200} />,
          ]),
          <Arrow key="a10" label="final prompt" />,
          col([
            row([
              <B key="cg" k="coverGeneration" width={160} />,
            ]),
            gap(8),
            row([
              <B key="ig" k="illustrationGeneration" width={160} />,
            ]),
          ]),
        ], { alignItems: "flex-start", marginBottom: 8 })}
        {gap(4)}
        {row([
          <div key="sp2" style={{ width: 200 }} />,
          gap(32 + 14),
          <div key="note3" style={{ fontSize: 11, color: COLORS.new, fontWeight: 600, lineHeight: 1.5, padding: "6px 10px", background: COLORS.newBg, border: `1px solid ${COLORS.newBorder}`, borderRadius: 6, maxWidth: 300 }}>
            Natural language instruction: "take this cover but replace the character with the main protagonist of my book" → Prompt Engineering merges I2T template with character.physical_description + visual_tokens
          </div>
        ])}
        {gap(16)}

        {/* ── ROW 5: Conditioning ── */}
        <SectionHeader>5 · Image Conditioning (Visual Bible → T2I)</SectionHeader>
        {row([
          <B key="vbdb2" k="visualBibleDB" width={170} />,
          <Arrow key="a11" label="reference images" />,
          col([
            <div key="lbl" style={{ fontSize: 11, color: "#888", marginBottom: 4 }}>Image conditioning</div>,
            row([
              <B key="cg2" k="coverGeneration" width={155} />,
              gap(8),
              <B key="ig2" k="illustrationGeneration" width={155} />,
            ]),
          ]),
        ], { marginBottom: 8 })}
        {row([
          <div key="sp3" style={{ maxWidth: 400, fontSize: 11, color: "#666", lineHeight: 1.6, padding: "8px 12px", background: "#f0f0f0", borderRadius: 6 }}>
            Artefact reference images (Visual Bible) passed as FLUX Kontext image conditioning for both cover and illustration generation. Character/location references used for illustration consistency. Cover references are handled via I2T path (text prompt), not direct image conditioning, to avoid copyright issues with third-party covers.
          </div>
        ])}
        {gap(16)}

        {/* ── ROW 6: Output ── */}
        <SectionHeader>6 · Output & Finishing</SectionHeader>
        {row([
          col([
            <B key="cs" k="coverStudio" width={170} />,
            <Arrow key="a12" vertical />,
            <B key="tc" k="typographyCompositor" width={170} />,
            <Arrow key="a13" vertical />,
            <Box key="dl" label="Download final cover PNG" type="user" width={170} />,
          ]),
          gap(40),
          col([
            <B key="ig3" k="illustrationGeneration" width={170} />,
            <Arrow key="a14" vertical />,
            <Box key="rp" label="Reading Page with illustrations" type="user" width={170} />,
          ]),
        ], { alignItems: "flex-start" })}

        {gap(32)}

        {/* ── Summary table ── */}
        <SectionHeader>Module Summary</SectionHeader>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
          <thead>
            <tr style={{ background: "#f0f0f0" }}>
              {["Module", "Status", "Key responsibility", "Phase"].map(h => (
                <th key={h} style={{ padding: "8px 12px", textAlign: "left", fontWeight: 700, color: "#555", borderBottom: "2px solid #ddd" }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {[
              ["Manuscript Upload & Chunking", "Built", "File ingestion, text extraction, chunking", "1"],
              ["AI Analysis Engine", "Built", "Extract characters, locations, artefacts, cover brief", "1–6"],
              ["Entity Database", "Built", "Store entities with visual tokens, ontology, selections", "1–6"],
              ["Analysis Review UI", "Built (gaps Phase 7)", "User reviews and selects main entities", "5–7"],
              ["Reference Search Engine", "Built + Pivot", "Multi-provider image search; add Serper", "6 + new"],
              ["Moodboard & Reference Selector", "Built + Pivot", "Image selection; add I2T trigger for covers", "6 + new"],
              ["Visual Bible DB", "Built", "Approved reference images per entity for T2I conditioning", "6"],
              ["I2T Analysis Service", "New", "GPT-4o Vision → style template from reference image", "New"],
              ["Prompt Engineering Service", "New", "Merge I2T template + entity context → final prompt", "New"],
              ["Cover Generation", "Stub → implement", "FLUX/DALL-E with I2T prompt + VB conditioning", "9"],
              ["Illustration Generation", "New (future)", "Scene illustrations with style + entity conditioning", "Future"],
              ["Cover Studio UI", "New", "View/select generated concepts, adjust brief", "13"],
              ["Typography Compositor", "New", "Browser-side text overlay → flattened PNG export", "13"],
            ].map(([mod, status, resp, phase], i) => (
              <tr key={mod} style={{ background: i % 2 === 0 ? "#fff" : "#fafafa" }}>
                <td style={{ padding: "7px 12px", fontWeight: 600, color: "#222", borderBottom: "1px solid #eee" }}>{mod}</td>
                <td style={{ padding: "7px 12px", borderBottom: "1px solid #eee" }}>
                  <span style={{ padding: "2px 7px", borderRadius: 4, fontSize: 11, fontWeight: 600, background: status.startsWith("Built") ? COLORS.builtBg : status.startsWith("New") ? COLORS.newBg : status.startsWith("Stub") ? COLORS.pivotBg : COLORS.pivotBg, color: status.startsWith("Built") ? COLORS.built : status.startsWith("New") ? COLORS.new : COLORS.pivot }}>
                    {status}
                  </span>
                </td>
                <td style={{ padding: "7px 12px", color: "#555", borderBottom: "1px solid #eee" }}>{resp}</td>
                <td style={{ padding: "7px 12px", color: "#888", borderBottom: "1px solid #eee" }}>{phase}</td>
              </tr>
            ))}
          </tbody>
        </table>

      </div>

      <InfoPanel node={activeNode ? NODES[activeNode] : null} onClose={() => setActiveNode(null)} />
    </div>
  );
}
