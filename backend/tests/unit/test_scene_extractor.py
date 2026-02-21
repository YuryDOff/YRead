"""
Unit tests for scene_extractor.group_chunks_into_candidate_scenes().
Pure deterministic logic — no LLM calls.
"""
import pytest

try:
    from app.services.scene_extractor import group_chunks_into_candidate_scenes
    SCENE_EXTRACTOR_AVAILABLE = True
except ImportError:
    SCENE_EXTRACTOR_AVAILABLE = False


def make_chunk(idx, dramatic, density, chars, narrative_pos="rising_action"):
    return {
        "chunk_index": idx,
        "dramatic_score": dramatic,
        "visual_density": density,
        "characters_present": chars,
        "locations_present": ["Lab"],
        "narrative_position": narrative_pos,
    }


# Build a 20-chunk test corpus
CHUNKS_20 = (
    [make_chunk(i, 0.3, "low",    ["Alice"])               for i in range(5)] +
    [make_chunk(i, 0.8, "high",   ["Alice", "Bob"],  "climax") for i in range(5, 10)] +
    [make_chunk(i, 0.4, "medium", ["Alice"])               for i in range(10, 15)] +
    [make_chunk(i, 0.9, "high",   ["Alice", "Bob", "Carol"], "climax") for i in range(15, 20)]
)


@pytest.mark.skipif(not SCENE_EXTRACTOR_AVAILABLE, reason="scene_extractor.py not yet implemented (Step 6)")
def test_returns_correct_scene_count():
    candidates = group_chunks_into_candidate_scenes(CHUNKS_20, scene_count=3)
    # Should return scene_count * 1.2 = ~4 candidates (buffer for LLM)
    assert len(candidates) >= 3


@pytest.mark.skipif(not SCENE_EXTRACTOR_AVAILABLE, reason="scene_extractor.py not yet implemented (Step 6)")
def test_high_drama_chunks_selected_over_low():
    candidates = group_chunks_into_candidate_scenes(CHUNKS_20, scene_count=2)
    for c in candidates:
        assert c["composite_score"] > 0.3, f"Low-drama window selected: {c}"


@pytest.mark.skipif(not SCENE_EXTRACTOR_AVAILABLE, reason="scene_extractor.py not yet implemented (Step 6)")
def test_no_overlapping_windows():
    candidates = group_chunks_into_candidate_scenes(CHUNKS_20, scene_count=4)
    ranges = [(c["chunk_start"], c["chunk_end"]) for c in candidates]
    for i, (s1, e1) in enumerate(ranges):
        for j, (s2, e2) in enumerate(ranges):
            if i == j:
                continue
            overlap = min(e1, e2) - max(s1, s2)
            window_min = min(e1 - s1, e2 - s2)
            assert overlap <= window_min * 0.5, \
                f"Windows {i} and {j} overlap too much: {s1}-{e1} vs {s2}-{e2}"


@pytest.mark.skipif(not SCENE_EXTRACTOR_AVAILABLE, reason="scene_extractor.py not yet implemented (Step 6)")
def test_each_window_covers_3_to_7_chunks():
    candidates = group_chunks_into_candidate_scenes(CHUNKS_20, scene_count=3)
    for c in candidates:
        span = c["chunk_end"] - c["chunk_start"] + 1
        assert 3 <= span <= 7, f"Window span {span} out of range 3-7"


@pytest.mark.skipif(not SCENE_EXTRACTOR_AVAILABLE, reason="scene_extractor.py not yet implemented (Step 6)")
def test_single_chunk_corpus_does_not_crash():
    single = [make_chunk(0, 0.9, "high", ["Alice", "Bob"])]
    result = group_chunks_into_candidate_scenes(single, scene_count=2)
    assert isinstance(result, list)
