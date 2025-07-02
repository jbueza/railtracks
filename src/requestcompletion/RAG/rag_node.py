from requestcompletion.RAG.rag_core import RAG
from requestcompletion import Node
import requestcompletion as rc

class RAGNode(Node):
    def __init__(self, documents: list, query: str) -> list:
        self.rag_core = RAG(
            docs=documents,
            embed_config={
                "model": "text-embedding-3-small",
            },
            store_config={},
            chunk_config={"chunk_size": 100, "chunk_overlap": 20, "model": "gpt-4o"},
        )

        self.rag_core.embed_all()
        result = self.rag_core.search(query, top_k=2)
        print(query)
        print(result)
        self.result = result

    @classmethod
    def pretty_name(cls) -> str:
        return "Easy RAG Node"

    def invoke(self)-> list:
        return self.result

def easy_rag_function(documents:list):
    class RAGNodeMini(Node):
        def __init__(self, query: str) -> list:
            self.rag_core = RAG(
                docs=documents,
                embed_config={
                    "model": "text-embedding-3-small",
                },
                store_config={},
                chunk_config={"chunk_size": 100, "chunk_overlap": 20, "model": "gpt-4o"},
            )

            self.rag_core.embed_all()
            result = self.rag_core.search(query, top_k=2)
            print(query)
            print(result)
            self.result = result

        @classmethod
        def pretty_name(cls) -> str:
            return "Easy RAG Node"

        def invoke(self)-> list:
            return self.result

    return RAGNodeMini

class EasyRAGClass:
    def __init__(self, documents: list) -> None:
        self.rag_core = RAG(
            docs=documents,
            embed_config={
                "model": "text-embedding-3-small",
            },
            store_config={},
            chunk_config={"chunk_size": 100, "chunk_overlap": 20, "model": "gpt-4o"},
        )
        self.rag_core.embed_all()

    def __call__(self):
        rag_core = self.rag_core
        class RAGNodeMini(Node):
            def __init__(self, query) -> list:

                result = rag_core.search(query, top_k=2)
                print(query)
                print(result)
                self.result = result

            @classmethod
            def pretty_name(cls) -> str:
                return "Easy RAG Node"

            def invoke(self)-> list:
                return self.result

        return RAGNodeMini

if __name__ == "__main__":
    docs = [
        "Apple is deep red",
        "Pear is light yellow",
        "Watermelon is green on the outside and red on the inside",
    ]
    query = "What is the color of watermelon?"
    # old function way
    easy_rag_func = easy_rag_function(documents=docs)
    with rc.Runner() as runner:
        response = rc.call(easy_rag_func, query=query)
    # new class way
    easy_rag_agent = EasyRAGClass(
        documents=docs
    )
    easy_rag_agent = easy_rag_agent()
    with rc.Runner() as runner:
        response = rc.call(easy_rag_agent, query=query)

    print("response:", response)
