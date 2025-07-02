from requestcompletion import RAG

def test_rag():
    rag = RAG(
        docs=[
            "Apple is deep red",
            "Pear is light yellow",
            "Watermelon is green on the outside and red on the inside",
        ],
        embed_config={
            "model": "text-embedding-3-small",
        },
        store_config={},
        chunk_config={"chunk_size": 100, "chunk_overlap": 20, "model": "gpt-4o"},
    )

    rag.embed_all()
    q= "What is Apple color?"
    print(q)
    print(rag.search(q, top_k=2))
    
if __name__ == "__main__":
    test_rag()
