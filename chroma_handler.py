import yaml
import os
import json
import chromadb
from datetime import datetime




with open('config.yaml', 'r') as f:
    cfg = yaml.safe_load(f)

class ChromaDB():
    chroma_persist_dir = cfg.get('embedding').get('chroma_persist_directory')
    def __init__(self):
        self.chroma_persist_dir = self.chroma_persist_dir

    def create_vector_embedding(self, input):
        from openai import OpenAI 
        from dotenv import load_dotenv
        load_dotenv()
        openai_api_key = os.getenv("OPENAI_API_KEY")
        openai_embedding_model = cfg.get('embedding', {}).get('openAI_embedding_model')

        # Create embedding using OpenAI API
        client = OpenAI(api_key=openai_api_key)
        response = client.embeddings.create(
            input=input,
            model=openai_embedding_model
        )
        # Prepare metadata, filtering out None values

        
        return response.data[0].embedding  

    @classmethod
    def _count_total_embeddings(cls):
        client = chromadb.PersistentClient(cls.chroma_persist_dir) # type: ignore
        total_embeddings = 0
        for collection in client.list_collections():
            coll = client.get_collection(collection.name)
            total_embeddings += coll.count()
        print(f"Total embeddings in ChromaDB: {total_embeddings}")

    def add_embedding_to_db(self, text, file_name, business_object, source_type):
        import hashlib 
        from langchain_text_splitters import TokenTextSplitter

        text_splitter = TokenTextSplitter(
            chunk_size=cfg.get('embedding', {}).get('max_chunk_size'),
            chunk_overlap=cfg.get('embedding', {}).get('chunk_overlap'),
        )

        raw_chunks = text_splitter.split_text(text)

        # Initialize ChromaDB client with persistence
        client = chromadb.PersistentClient(  # type: ignore
            path=self.chroma_persist_dir
        )

        # Decide collection name once
        if source_type == "API":
            collection_name = "API_embeddings"
        elif source_type == "DB":
            collection_name = "DB_embeddings"
        elif source_type == "TXT":
            collection_name = "TXT_embeddings"
        else:
            raise ValueError(f"Unknown source type: {source_type}")

        collection = client.get_or_create_collection(name=collection_name)

        # Ensure the JSON dump folder exists: <persist_dir>/<collection_name>
        json_out_dir = os.path.join(self.chroma_persist_dir, collection_name)
        os.makedirs(json_out_dir, exist_ok=True)

        for i, raw_chunk in enumerate(raw_chunks, start=1):
            embedding = self.create_vector_embedding(raw_chunk)

            metadata = {
                k: v for k, v in {
                    "id": hashlib.sha256(str(raw_chunk).encode("utf-8")).hexdigest(),
                    "file_name": file_name,
                    "business_object": business_object,
                    "source_type": source_type,
                }.items() if v is not None
            }

            record = {
                "id": metadata["id"],
                "chunk_index": i,
                "text": raw_chunk,
                "embedding": embedding,
                "metadata": metadata,
                "created_at": datetime.utcnow().isoformat() + "Z",
            }

            json_path = os.path.join(json_out_dir, f"{metadata['id']}.json")
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(record, f, ensure_ascii=False)

            # --- Existing: store in Chroma collection ---
            collection.add(
                ids=metadata.get('id'),          # type: ignore
                embeddings=embedding,
                documents=raw_chunk,
                metadatas=[metadata]             # type: ignore
            )

    def evaluate_relevance(self, chunk, user_input, initial_system_prompt):
        from llm_handler import LLMQuery
        relevance_system_prompt = """You are an expert whose task is to critique how relevant a single retrieved system documentation chunk is to a user's query. You will be given three inputs: "General Task", "User Query" and "Retrieved System Documentation".

Return a single true or false based on the relevance score.
- relevance_score: number 0.0-1.0 - degree of semantic and pragmatic relevance (1.0 = completely relevant; 0.0 = completely irrelevant).
if relevance_score >= 0.2: return true 
else: return false

Constraints:
- Be concise and factual. Do not introduce new domain facts or attempt to answer the query.
- Use only information present in the chunk and the query to form your judgment.
- Keep your response strictly as a boolean value (no extra commentary outside the boolean)."""


        query = LLMQuery("a", "b")
        general_task = initial_system_prompt
        user_prompt = "General Task: {}\n\nUser Query: {}\n\nRetrieved System Documentation: {}".format(general_task, user_input, chunk)
        relevant = query.process(system_prompt=relevance_system_prompt, user_prompt=user_prompt)

        return relevant
            

    def retrieve(self, query_text, top_n_entries=None):
        knowledge_basis = cfg.get('process_orchestration').get('knowledge_basis').upper()
        if top_n_entries is None:
            top_n_entries = cfg.get('embedding', {}).get('top_n_entries')
        input_embedding = self.create_vector_embedding(query_text)

        chroma_client = chromadb.PersistentClient(self.chroma_persist_dir) 
        
        if knowledge_basis == "DB":
            collections = ["DB_embeddings", "TXT_embeddings"]
        elif knowledge_basis == "API":
            collections = ["API_embeddings", "TXT_embeddings"]
        else:
            collections = [col.name for col in chroma_client.list_collections()]
        results = []
        for collection_name in collections:
            collection = chroma_client.get_collection(collection_name)
            query_result = collection.query(
                query_embeddings=[input_embedding],
                n_results=top_n_entries
            )
            # collect rows
            for i in range(len(query_result["ids"][0])):
                results.append({
                    "collection": collection_name,
                    "id": query_result["ids"][0][i],
                    "document": (query_result.get("documents") or [[]])[0][i] if query_result.get("documents") else None,
                    "metadata": (query_result.get("metadatas") or [[]])[0][i] if query_result.get("metadatas") else None,
                    "distance": (query_result.get("distances") or [[]])[0][i] if query_result.get("distances") else None,
                })
              
        # Sort all results by distance (ascending)
        results.sort(key=lambda x: x['distance'])
        
        # Return top n closest entries across all collections
        if knowledge_basis == "NONE":
            top_n_entries = 0

        return results[:top_n_entries]