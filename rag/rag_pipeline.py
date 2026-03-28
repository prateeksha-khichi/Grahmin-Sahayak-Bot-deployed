"""
RAG Pipeline - End-to-end RAG workflow
Orchestrates PDF loading, chunking, embedding, indexing, and retrieval
"""

from typing import Dict
from loguru import logger

from .pdf_loader import PDFLoader
from .chunker import TextChunker
from .embedder import Embedder
from .vector_store import VectorStore
from .retriever import Retriever
from .prompt import PromptTemplate


class RAGPipeline:
    """
    Complete RAG pipeline for document Q&A
    """

    def __init__(self, pdf_directory: str = "data/pdfs"):
        self.pdf_directory = pdf_directory

        # Initialize components
        self.pdf_loader = PDFLoader(pdf_directory)
        self.chunker = TextChunker()
        self.embedder = Embedder()
        self.vector_store = VectorStore()
        self.retriever = None
        self.prompt_template = PromptTemplate()

        self.is_indexed = False

    def build_index(self, force_rebuild: bool = False):
        """
        Build FAISS index in a MEMORY-SAFE streaming manner
        """

        # Try loading existing index
        if not force_rebuild and self.vector_store.load():
            logger.info("✅ Loaded existing index")
            self.retriever = Retriever(self.vector_store, self.embedder)
            self.is_indexed = True
            return

        logger.info("🔄 Building new index (memory-safe mode)...")

        # Step 1: Load PDFs
        logger.info("📚 Step 1/4: Loading PDFs...")
        documents = self.pdf_loader.load_all_pdfs()

        if not documents:
            logger.error("❌ No PDFs found! Please add PDFs to data/pdfs/")
            return

        total_chunks = 0

        # Step 2–4: Process ONE document at a time
        for i, doc in enumerate(documents, start=1):
            logger.info(
                f"✂️ Processing document {i}/{len(documents)}: {doc.get('filename', 'unknown')}"
            )

            # Step 2: Chunk document
            chunks = self.chunker.chunk_document(doc)
            if not chunks:
                continue

            texts = [c["text"] for c in chunks]

            # Step 3: Generate embeddings in small batches
            embeddings = self.embedder.embed_chunks(
                texts,
                batch_size=32
            )

            # Step 4: Incrementally add to vector store
            self.vector_store.add(embeddings, chunks)

            total_chunks += len(chunks)

            # Explicit cleanup (important on Windows)
            del chunks, texts, embeddings

        # Save index once
        self.vector_store.save()

        # Initialize retriever
        self.retriever = Retriever(self.vector_store, self.embedder)
        self.is_indexed = True

        logger.info("✅ Index built successfully!")
        logger.info(f"📊 Total chunks indexed: {total_chunks}")

    def query(
        self,
        question: str,
        language: str = "hindi",
        top_k: int = 3
    ) -> Dict[str, any]:
        """
        Query the RAG system
        """

        if not self.is_indexed:
            logger.warning("⚠️ Index not built. Building now...")
            self.build_index()

        if not self.is_indexed:
            return {
                "context": "",
                "sources": [],
                "prompt": self.prompt_template.get_no_context_prompt(question),
                "retrieved_chunks": []
            }

        # Retrieve relevant chunks
        results = self.retriever.retrieve(question, top_k=top_k)

        if not results:
            return {
                "context": "",
                "sources": [],
                "prompt": self.prompt_template.get_no_context_prompt(question),
                "retrieved_chunks": []
            }

        # Format context
        context = self.retriever.retrieve_with_context(question, top_k=top_k)

        # Extract sources
        sources = list(set(r["source"] for r in results))

        # Generate final prompt
        prompt = self.prompt_template.get_rag_prompt(
            question,
            context,
            language
        )

        return {
            "context": context,
            "sources": sources,
            "prompt": prompt,
            "retrieved_chunks": results
        }

    def explain_scheme(self, scheme_name: str, top_k: int = 5) -> str:
        """
        Explain a government scheme
        """
        if not self.is_indexed:
            self.build_index()

        results = self.retriever.retrieve(scheme_name, top_k=top_k)
        context = "\n\n".join(r["text"] for r in results)

        return self.prompt_template.get_scheme_explanation_prompt(
            scheme_name,
            context
        )

    def explain_term(self, term: str, top_k: int = 3) -> str:
        """
        Explain a banking/financial term
        """
        if not self.is_indexed:
            self.build_index()

        results = self.retriever.retrieve(term, top_k=top_k)
        context = "\n\n".join(r["text"] for r in results)

        return self.prompt_template.get_term_explanation_prompt(
            term,
            context
        )

    def get_stats(self) -> Dict[str, any]:
        """
        Get pipeline statistics
        """
        if not self.is_indexed:
            return {"status": "not_indexed"}

        return {
            "status": "indexed",
            "total_vectors": self.vector_store.index.ntotal,
            "dimension": self.embedder.dimension,
            "total_chunks": len(self.vector_store.chunks),
            "pdf_directory": self.pdf_directory
        }


# CLI entry point
if __name__ == "__main__":
    import sys

    logger.info("🚀 Gramin Sahayak RAG Pipeline")

    pipeline = RAGPipeline()

    if len(sys.argv) > 1 and sys.argv[1] == "--rebuild":
        logger.info("🔨 Forcing index rebuild...")
        pipeline.build_index(force_rebuild=True)
    else:
        pipeline.build_index()

    print("\n" + "=" * 60)
    print("✅ RAG Pipeline Ready!")
    print("Type your questions (or 'quit' to exit)")
    print("=" * 60 + "\n")

    while True:
        try:
            query = input("🤔 आपका प्रश्न (Your question): ").strip()

            if query.lower() in {"quit", "exit", "q"}:
                break

            if not query:
                continue

            result = pipeline.query(query, language="hindi")

            print("\n" + "-" * 60)
            print("📚 Context Retrieved:")
            print(
                result["context"][:500] + "..."
                if len(result["context"]) > 500
                else result["context"]
            )
            print("\n📄 Sources:", ", ".join(result["sources"]))
            print("\n💬 Prompt for LLM:")
            print(result["prompt"][:300] + "...")
            print("-" * 60 + "\n")

        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error(f"❌ Error: {e}")

    logger.info("👋 Goodbye!")
