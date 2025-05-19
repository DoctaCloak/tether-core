from typing import List, Optional, Dict, Any
import chromadb
from chromadb.utils import embedding_functions # For generating embeddings if needed
import uuid
from datetime import datetime, timezone

from .store_interface import VectorStoreInterface
from .models import Echo, EchoCreate, EchoFilter

# Configuration for ChromaDB (example)
CHROMA_PATH = "./chroma_data"  # Path for on-disk persistence
CHROMA_COLLECTION_NAME = "tether_echos"
# To use a default sentence transformer for embeddings with Chroma:
# You might need to install sentence-transformers: pip install sentence-transformers
# DEFAULT_EMBEDDING_FUNCTION = embedding_functions.DefaultEmbeddingFunction()


class ChromaStore(VectorStoreInterface):
    """
    ChromaDB implementation of the VectorStoreInterface.
    """
    client: Optional[chromadb.Client] = None
    collection: Optional[chromadb.Collection] = None

    def __init__(self, path: str = CHROMA_PATH, collection_name: str = CHROMA_COLLECTION_NAME):
        self.path = path
        self.collection_name = collection_name
        # For in-memory: self.client = chromadb.Client()
        # For persistent:
        self.client = chromadb.PersistentClient(path=self.path)
        print(f"ChromaStore initialized for path: {self.path}, collection: {self.collection_name}")

    async def connect(self):
        """Connect to ChromaDB (client is initialized in __init__, get/create collection here)."""
        if self.collection:
            print("Already connected to Chroma collection.")
            return
        try:
            # Get or create the collection.
            # You might want to specify an embedding function if Chroma isn't configured globally
            # or if you want a specific one for this collection.
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                # embedding_function=DEFAULT_EMBEDDING_FUNCTION # Optional
            )
            print(f"Successfully connected to Chroma collection: '{self.collection_name}'")
            await self.ensure_schema() # Chroma schema is more about collection existence
        except Exception as e:
            print(f"Error connecting to Chroma collection: {e}")
            self.collection = None
            raise

    async def disconnect(self):
        """Chroma client does not have an explicit disconnect. Resources are managed by the client."""
        print("Chroma client does not require explicit disconnect.")
        # self.client.clear_system_cache() # Optional, if issues arise
        self.collection = None # Allow garbage collection

    async def ensure_schema(self):
        """
        For Chroma, 'schema' is primarily about the existence of the collection
        and its configuration (like embedding function if specified at creation).
        Individual fields are stored in metadata.
        """
        if not self.collection:
            # This should ideally be called after connect() ensures collection exists
            print("Collection not available. Call connect() first.")
            await self.connect()
            if not self.collection:
                raise ConnectionError("Failed to connect to Chroma to ensure schema.")
        print(f"Chroma schema (collection '{self.collection_name}') is considered ensured if collection exists.")

    def _echo_to_chroma_doc(self, echo: EchoCreate, echo_id: str) -> Dict[str, Any]:
        """Helper to convert EchoCreate to Chroma document format (metadata, document content)."""
        metadata = {
            "user_id": echo.user_id,
            "created_at": echo.created_at.isoformat(),
            "updated_at": echo.updated_at.isoformat(),
            # Store tags as a single string or handle them carefully if filtering is needed
            # Chroma metadata values must be string, int, float, or bool.
            # For list of tags, you might join them or handle complex queries differently.
            "tags_str": ",".join(sorted(list(set(echo.tags)))) if echo.tags else "",
        }
        # Add other flat metadata if present
        # if echo.metadata:
        #     for k, v in echo.metadata.items():
        #         if isinstance(v, (str, int, float, bool)):
        #             metadata[k] = v
        return {"id": echo_id, "document": echo.content, "metadata": metadata}

    def _chroma_doc_to_echo(self, doc_id: str, document_content: Optional[str], metadata: Optional[Dict[str, Any]]) -> Echo:
        """Helper to convert Chroma document format back to Echo."""
        if metadata is None:
            metadata = {}
        tags_str = metadata.get("tags_str", "")
        tags_list = [tag for tag in tags_str.split(',') if tag] if tags_str else []

        return Echo(
            id=doc_id,
            content=document_content or "",
            tags=tags_list,
            user_id=metadata.get("user_id", "unknown_user"),
            created_at=datetime.fromisoformat(metadata["created_at"]) if "created_at" in metadata else datetime.now(timezone.utc),
            updated_at=datetime.fromisoformat(metadata["updated_at"]) if "updated_at" in metadata else datetime.now(timezone.utc),
            # metadata={k: v for k, v in metadata.items() if k not in ["user_id", "created_at", "updated_at", "tags_str"]}
        )

    async def add_echo(self, echo_data: EchoCreate) -> Echo:
        """Adds a new Echo to Chroma."""
        if not self.collection:
            raise ConnectionError("Chroma collection not available. Call connect() first.")

        echo_id = str(uuid.uuid4())
        chroma_doc = self._echo_to_chroma_doc(echo_data, echo_id)

        try:
            self.collection.add(
                ids=[chroma_doc["id"]],
                documents=[chroma_doc["document"]], # Document to be embedded
                metadatas=[chroma_doc["metadata"]]
            )
            return self._chroma_doc_to_echo(echo_id, echo_data.content, chroma_doc["metadata"])
        except Exception as e:
            print(f"Error adding Echo to Chroma: {e}")
            raise

    async def get_echo(self, echo_id: str) -> Optional[Echo]:
        """Retrieves a specific Echo by its ID from Chroma."""
        if not self.collection:
            raise ConnectionError("Chroma collection not available.")
        try:
            results = self.collection.get(ids=[echo_id], include=["metadatas", "documents"])
            if results and results['ids']:
                doc_id = results['ids'][0]
                doc_content = results['documents'][0] if results['documents'] else None
                metadata = results['metadatas'][0] if results['metadatas'] else None
                return self._chroma_doc_to_echo(doc_id, doc_content, metadata)
            return None
        except Exception as e: # Chroma might raise specific errors for not found
            print(f"Error getting Echo {echo_id} from Chroma: {e}")
            return None

    async def list_echos(self, filters: Optional[EchoFilter] = None, limit: int = 100, offset: int = 0) -> List[Echo]:
        """Lists Echos from Chroma, optionally applying filters."""
        if not self.collection:
            raise ConnectionError("Chroma collection not available.")

        where_filter: Optional[Dict[str, Any]] = None
        if filters:
            # Chroma's where filter is a dict, e.g., {"user_id": "user123"}
            # For tags, if stored as "tags_str", you might need to use $contains or other operators
            # if your Chroma version supports advanced metadata filtering.
            # This is a simplified example.
            temp_filter = {}
            if filters.user_id:
                temp_filter["user_id"] = filters.user_id
            # if filters.tags_include_all: # Complex for comma-separated string
            #    # This would require more advanced query or post-filtering
            #    print("Warning: Complex tag filtering not fully supported by this basic ChromaStore list_echos.")
            if temp_filter:
                where_filter = temp_filter
            print(f"Filtering with: {where_filter}. Filters received: {filters}")


        try:
            results = self.collection.get(
                where=where_filter,
                limit=limit,
                offset=offset,
                include=["metadatas", "documents"]
            )
            echos = []
            if results and results['ids']:
                for i, doc_id in enumerate(results['ids']):
                    doc_content = results['documents'][i] if results['documents'] else None
                    metadata = results['metadatas'][i] if results['metadatas'] else None
                    echos.append(self._chroma_doc_to_echo(doc_id, doc_content, metadata))
            return echos
        except Exception as e:
            print(f"Error listing Echos from Chroma: {e}")
            return []

    async def update_echo(self, echo_id: str, echo_update_data: Dict[str, Any]) -> Optional[Echo]:
        """Updates an existing Echo in Chroma (effectively add/replace)."""
        if not self.collection:
            raise ConnectionError("Chroma collection not available.")

        # Get existing to merge, as Chroma's 'add' with same ID updates.
        # Or, if 'upsert' is used, it handles this.
        # Let's assume we need to reconstruct the full object for update.
        # This is simplified; a real update might need careful metadata merging.
        print(f"Updating Echo {echo_id}. Data: {echo_update_data}. This is an upsert operation.")
        # For a true partial update, you'd fetch, modify, then re-add/upsert.
        # Here, we'll assume echo_update_data can be used to form a new EchoCreate-like object.

        # This is a simplified upsert. You might need to fetch the existing document
        # to properly merge metadata or handle partial updates.
        try:
            # For simplicity, let's assume echo_update_data contains all necessary fields
            # or that we are doing a full replacement of document and metadata.
            # A more robust solution would fetch the existing record, update fields, then upsert.
            if "content" not in echo_update_data or "user_id" not in echo_update_data:
                 print("Warning: Chroma update expects full document content and user_id for this simplified upsert.")
                 # Fetch existing to get missing parts if needed
                 existing_echo = await self.get_echo(echo_id)
                 if not existing_echo:
                     return None
                 
                 updated_content = echo_update_data.get("content", existing_echo.content)
                 updated_tags = echo_update_data.get("tags", existing_echo.tags) # Assuming tags are passed as list
                 updated_user_id = echo_update_data.get("user_id", existing_echo.user_id)
            else:
                updated_content = echo_update_data["content"]
                updated_tags = echo_update_data.get("tags", [])
                updated_user_id = echo_update_data["user_id"]


            new_metadata = {
                "user_id": updated_user_id,
                "created_at": echo_update_data.get("created_at", datetime.now(timezone.utc).isoformat()), # Or keep original
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "tags_str": ",".join(sorted(list(set(updated_tags)))) if updated_tags else "",
            }

            self.collection.upsert(
                ids=[echo_id],
                documents=[updated_content],
                metadatas=[new_metadata]
            )
            return await self.get_echo(echo_id) # Fetch the updated record
        except Exception as e:
            print(f"Error updating Echo {echo_id} in Chroma: {e}")
            return None


    async def delete_echo(self, echo_id: str) -> bool:
        """Deletes an Echo from Chroma."""
        if not self.collection:
            raise ConnectionError("Chroma collection not available.")
        try:
            self.collection.delete(ids=[echo_id])
            return True
        except Exception as e: # Chroma might raise specific errors
            print(f"Error deleting Echo {echo_id} from Chroma: {e}")
            return False

    async def search_echos_by_vector(self, vector: List[float], limit: int = 10, filters: Optional[EchoFilter] = None) -> List[Echo]:
        """Searches Echos by vector similarity."""
        if not self.collection:
            raise ConnectionError("Chroma collection not available.")

        where_filter: Optional[Dict[str, Any]] = None
        if filters:
            # Similar to list_echos, build a where_filter if needed
            temp_filter = {}
            if filters.user_id: temp_filter["user_id"] = filters.user_id
            if temp_filter: where_filter = temp_filter
            print(f"Filtering for vector search: {where_filter}. Filters: {filters}")


        try:
            results = self.collection.query(
                query_embeddings=[vector],
                n_results=limit,
                where=where_filter,
                include=["metadatas", "documents", "distances"]
            )
            echos = []
            if results and results['ids'] and results['ids'][0]: # query returns a list of lists
                for i, doc_id in enumerate(results['ids'][0]):
                    doc_content = results['documents'][0][i] if results['documents'] and results['documents'][0] else None
                    metadata = results['metadatas'][0][i] if results['metadatas'] and results['metadatas'][0] else None
                    # distance = results['distances'][0][i] if results['distances'] and results['distances'][0] else None
                    echos.append(self._chroma_doc_to_echo(doc_id, doc_content, metadata))
            return echos
        except Exception as e:
            print(f"Error searching Echos by vector in Chroma: {e}")
            return []

    async def search_echos_by_text(self, query_text: str, limit: int = 10, filters: Optional[EchoFilter] = None) -> List[Echo]:
        """
        Searches Echos by text similarity.
        Requires the collection to have an embedding function that can process query_text.
        """
        if not self.collection:
            raise ConnectionError("Chroma collection not available.")

        where_filter: Optional[Dict[str, Any]] = None
        if filters:
            # Similar to list_echos, build a where_filter if needed
            temp_filter = {}
            if filters.user_id: temp_filter["user_id"] = filters.user_id
            if temp_filter: where_filter = temp_filter
            print(f"Filtering for text search: {where_filter}. Filters: {filters}")

        try:
            results = self.collection.query(
                query_texts=[query_text], # Chroma uses query_texts for this
                n_results=limit,
                where=where_filter,
                include=["metadatas", "documents", "distances"]
            )
            echos = []
            if results and results['ids'] and results['ids'][0]:
                for i, doc_id in enumerate(results['ids'][0]):
                    doc_content = results['documents'][0][i] if results['documents'] and results['documents'][0] else None
                    metadata = results['metadatas'][0][i] if results['metadatas'] and results['metadatas'][0] else None
                    echos.append(self._chroma_doc_to_echo(doc_id, doc_content, metadata))
            return echos
        except Exception as e:
            print(f"Error searching Echos by text in Chroma: {e}")
            return []

# Example of how to use (for testing)
async def _chroma_example():
    store = ChromaStore(path="./chroma_test_data") # Use a test path
    try:
        await store.connect()

        new_echo_data = EchoCreate(
            content="A test Echo for ChromaDB!",
            tags=["test", "chroma"],
            user_id="user_chroma_test",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        created_echo = await store.add_echo(new_echo_data)
        print(f"Chroma - Created Echo: {created_echo}")

        if created_echo:
            retrieved_echo = await store.get_echo(created_echo.id)
            print(f"Chroma - Retrieved Echo: {retrieved_echo}")

            all_echos = await store.list_echos(limit=5)
            print(f"Chroma - Listed Echos: {all_echos}")

            # Text search (ensure your collection has an appropriate embedding function)
            # search_results = await store.search_echos_by_text("test Chroma", limit=2)
            # print(f"Chroma - Search results (text): {search_results}")

            # await store.delete_echo(created_echo.id)
            # print(f"Chroma - Echo deleted: {await store.get_echo(created_echo.id) is None}")

    except Exception as e:
        print(f"An error occurred in Chroma example: {e}")
    finally:
        await store.disconnect()
        # Clean up test data directory if needed
        # import shutil
        # shutil.rmtree("./chroma_test_data", ignore_errors=True)


if __name__ == "__main__":
    # import asyncio
    # asyncio.run(_chroma_example()) # Commented out
    pass
