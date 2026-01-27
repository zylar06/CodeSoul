import os
import chromadb
from chromadb.config import Settings
from fastembed import TextEmbedding
from typing import List, Dict, Any
import asyncio
from .ingest import CodeChunk

class VectorDB:
    def __init__(self, persist_path: str = ".codesoul_db"):
        self.persist_path = persist_path
        # Use simple settings
        self.client = chromadb.PersistentClient(path=persist_path, settings=Settings(anonymized_telemetry=False))
        
        # Initialize embedding model (lightweight, runs on CPU)
        # BAAI/bge-small-en-v1.5 is excellent and small
        self.embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
        
        self.collection_name = "codebase_v1"
        self.collection = self.get_or_create_collection()

    def get_or_create_collection(self):
        return self.client.get_or_create_collection(name=self.collection_name)

    def reset_db(self):
        self.client.delete_collection(self.collection_name)
        self.collection = self.get_or_create_collection()

    async def add_chunks(self, chunks: List[CodeChunk], batch_size: int = 64):
        """
        Embed and store chunks. Runs in a thread to avoid blocking async loop.
        """
        if not chunks:
            return

        def _process():
            # Prepare data
            documents = [chunk.content for chunk in chunks]
            metadatas = [
                {
                    "file_path": chunk.file_path,
                    "start_line": chunk.start_line,
                    "end_line": chunk.end_line,
                    **chunk.metadata
                } 
                for chunk in chunks
            ]
            ids = [f"{chunk.file_path}:{chunk.start_line}" for chunk in chunks]

            # Generate embeddings using FastEmbed
            # This returns a generator, so we convert to list
            embeddings_generator = self.embedding_model.embed(documents)
            embeddings = list(embeddings_generator)

            # Add to Chroma (upsert to handle re-runs)
            self.collection.upsert(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
            
        await asyncio.to_thread(_process)

    async def query(self, query_text: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Semantic search.
        """
        def _search():
            # Embed the query
            query_embedding = list(self.embedding_model.embed([query_text]))[0]
            
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )
            
            # Flatten results structure
            flattened = []
            if results["ids"]:
                for i in range(len(results["ids"][0])):
                    flattened.append({
                        "id": results["ids"][0][i],
                        "document": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "distance": results["distances"][0][i] if results["distances"] else 0
                    })
            return flattened

        return await asyncio.to_thread(_search)

    def get_stats(self) -> Dict[str, Any]:
        return {
            "count": self.collection.count(),
            "persist_path": self.persist_path
        }
