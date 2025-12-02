import os
from typing import List, Dict, Any, Optional

try:
    from chromadb import PersistentClient
except Exception as e:
    raise ImportError("chromadb is required: pip install chromadb") from e

class VectorStore:
    """ 
    A simple vector store using ChromaDB for storing and querying embeddings.
    """
    
    def __init__(self, persist_dir: str = "data/vectorstore", collection_name: str = "transactions"):
        """
        Initialize the vector store with a persistent directory and collection name.
        """
        
        self.persist_dir = persist_dir
        self.collection_name = collection_name
        os.makedirs(self.persist_dir, exist_ok=True)
        self.client = PersistentClient(path=self.persist_dir)
        
        try:
            self.col = self.client.get_collection(name=self.collection_name)
        except Exception:
            self.col = self.client.create_collection(name=self.collection_name)

    def upsert(self, ids: List[str], embs: List[List[float]], docs: List[str], metadatas: List[Dict[str, Any]]):
        """ 
        Upsert embeddings and associated data into the vector store. 
        """
        
        self.col.upsert(
            ids=ids,
            embeddings=embs,
            documents=docs,
            metadatas=metadatas
        )

    def query_by_embedding(self, emb: List[float], n_results: int = 5) -> List[Dict[str, Any]]:
        """ 
        Query the vector store using an embedding vector.
        """
        
        res = self.col.query(query_embeddings=[emb], n_results=n_results)
        out = []
        ids = res.get("ids", [[]])[0]
        dists = res.get("distances", [[]])[0]
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        
        for i in range(len(ids)):
            out.append({
                "id": ids[i],
                "doc": docs[i] if i < len(docs) else None,
                "meta": metas[i] if i < len(metas) else None,
                "distance": dists[i] if i < len(dists) else None
            })
        
        return out

    def query_by_text(self, text: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """ 
        Query the vector store using a text string.
        """
        
        res = self.col.query(query_texts=[text], n_results=n_results)
        out = []
        ids = res.get("ids", [[]])[0]
        dists = res.get("distances", [[]])[0]
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        
        for i in range(len(ids)):
            out.append({
                "id": ids[i],
                "doc": docs[i] if i < len(docs) else None,
                "meta": metas[i] if i < len(metas) else None,
                "distance": dists[i] if i < len(dists) else None
            })
        
        return out
