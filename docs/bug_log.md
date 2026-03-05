# Noctua — Bug Log
> Living document. Never delete entries — update status instead.
> Severity: Critical (blocks release) | High (bad UX, workaround exists) | Low (cosmetic/minor)

---

## Bug Entry Template

```
## BUG-XXX
**Status:** Open | In Progress | Fixed
**Severity:** Critical | High | Low
**Found in:** [Phase / Page / Service]
**Reported:** YYYY-MM-DD
**Description:** What happens.
**Steps to reproduce:** 
  1. 
  2. 
**Expected:** What should happen.
**Fix notes:** —
**Fixed in:** [Phase X / commit ref] — fill when resolved
```

---

## Open Bugs

_No bugs logged yet. Add entries here as they are found._

---

## Fixed Bugs

### BUG-001
**Status:** Open
**Severity:** High
**Found in:**  AnalysisReviewPage — entity selection
**Description:** BUG-1 — is_main flag collision. Re-analysis was overwriting is_main to 0 on every run, losing user's entity selections.
**Expected:** is_main selections made by the user should persist across re-analysis runs.
**Fix notes:** is_main write separated from analysis write path in crud.py
**Fixed in:** Phase 7

### BUG-002 (from Phase 7)
**Status:** Fixed
**Severity:** Low
**Found in:** Phase 7 / Scenes — scene_display_count
**Description:** BUG-2 — scene display count not respected. All extracted scenes shown regardless of scene_display_count setting.
**Expected:** UI should respect scene_display_count from book settings.
**Fix notes:** GET /scenes now filters by scene_display_count; extraction count separate from display count
**Fixed in:** Phase 7

---

## Tracking Notes

### Severity guide
- **Critical:** App crashes, data loss, analysis fails to complete, cover generation broken
- **High:** Wrong output (wrong entities extracted, tokens incorrect), UI state corruption, broken navigation
- **Low:** Cosmetic issues, minor label errors, non-blocking UX friction

### How to use with Cursor Composer
When starting a new phase session, paste any Open bugs relevant to the files being touched. Prefix the bug entry with: *"Fix this bug as part of this phase if the fix is small (<30 min). Otherwise flag it."*
