from backend.services.chunker import chunk_section

def test_chunker_basic():
    text = " ".join([f"tok{i}" for i in range(0, 1000)])
    chunks = chunk_section("p1","s1",text, target_tokens=300, overlap_tokens=50, page_from=1, page_to=1)
    assert len(chunks) >= 3
    assert chunks[0]["chunk_id"].startswith("p1:s1:")
    assert all(len(c["text"]) > 0 for c in chunks)
