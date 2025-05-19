from typing import List, Optional, Dict, Any
import weaviate
import uuid # For generating IDs if not provided by Weaviate or if needed
from .store_interface import VectorStoreInterface
from .models import Echo, EchoCreate, EchoFilter

# Configuration for Weaviate connection (example)
WEAVIATE_URL = "http://localhost:8080" # Or from config
WEAVIATE_API_KEY = None # If using Weaviate Cloud Services (WCS)
ECHO_CLASS_NAME = "Echo" # Name of the class in Weaviate schema

class WeaviateStore(VectorStoreInterface):
    """
    Weaviate implementation of the VectorStoreInterface.
    """
    client: Optional[weaviate.Client] = None

    def __init__(self, url: str = WEAVIATE_URL, api_key: Optional[str] = WEAVIATE_API_KEY):
        self.url = url
        self.api_key = api_key
        print(f"WeaviateStore initialized for URL: {self.url}")

    async def connect(self):
        """Connect to the Weaviate instance."""
        if self.client and self.client.is_ready():
            print("Already connected to Weaviate.")
            return

        try:
            auth_config = None
            if self.api_key:
                auth_config = weaviate.auth.AuthApiKey(api_key=self.api_key)

            self.client = weaviate.Client(
                url=self.url,
                auth_client_secret=auth_config
            )
            if self.client.is_ready():
                print("Successfully connected to Weaviate.")
                await self.ensure_schema()
            else:
                print("Failed to connect to Weaviate after client initialization.")
                self.client = None # Reset client if not ready
        except Exception as e:
            print(f"Error connecting to Weaviate: {e}")
            self.client = None
            raise

    async def disconnect(self):
        """Disconnect from Weaviate (Weaviate client doesn't have an explicit disconnect)."""
        print("Weaviate client does not require explicit disconnect. Connection will close when object is destroyed or program exits.")
        self.client = None # Allow garbage collection

    async def ensure_schema(self):
        """Ensure the 'Echo' class schema exists in Weaviate."""
        if not self.client or not self.client.is_ready():
            print("Cannot ensure schema: Weaviate client not connected.")
            # Optionally, try to connect here or raise an error
            await self.connect() # Try to connect if not already
            if not self.client or not self.client.is_ready():
                 raise ConnectionError("Failed to connect to Weaviate to ensure schema.")


        schema = self.client.schema.get()
        class_exists = any(cls['class'] == ECHO_CLASS_NAME for cls in schema.get('classes', []))

        if not class_exists:
            print(f"'{ECHO_CLASS_NAME}' class not found in Weaviate. Creating schema...")
            echo_class_obj = {
                "class": ECHO_CLASS_NAME,
                "description": "Stores Echos (memories, thoughts, goals) for TetherCore",
                "vectorizer": "text2vec-transformers", # Example, choose your vectorizer
                # Or "vectorizer": "none" if you provide your own vectors
                "moduleConfig": {
                    "text2vec-transformers": { # Ensure this module is enabled in your Weaviate setup
                        "poolingStrategy": "masked_mean",
                        "vectorizeClassName": False # Usually False for custom classes
                    }
                },
                "properties": [
                    {"name": "content", "dataType": ["text"], "description": "Textual content of the Echo"},
                    {"name": "tags", "dataType": ["list[string]"], "description": "Tags associated with the Echo"}, # Weaviate uses string[]
                    {"name": "created_at", "dataType": ["date"], "description": "Timestamp of Echo creation"},
                    {"name": "updated_at", "dataType": ["date"], "description": "Timestamp of Echo last update"},
                    {"name": "user_id", "dataType": ["string"], "description": "ID of the user who owns the Echo"},
                    # Add other properties as defined in your Echo model
                ]
            }
            try:
                self.client.schema.create_class(echo_class_obj)
                print(f"Successfully created '{ECHO_CLASS_NAME}' class in Weaviate.")
            except Exception as e:
                print(f"Error creating '{ECHO_CLASS_NAME}' class: {e}")
                raise
        else:
            print(f"'{ECHO_CLASS_NAME}' class already exists in Weaviate.")


    async def add_echo(self, echo_data: EchoCreate) -> Echo:
        """Adds a new Echo to Weaviate."""
        if not self.client:
            raise ConnectionError("Weaviate client not connected. Call connect() first.")

        properties = {
            "content": echo_data.content,
            "tags": echo_data.tags or [],
            "created_at": echo_data.created_at.isoformat(),
            "updated_at": echo_data.updated_at.isoformat(),
            "user_id": echo_data.user_id,
            # **echo_data.metadata if echo_data.metadata else {} # Spread metadata if it's flat
        }
        # If you are providing your own vectors, add the 'vector' key here
        # vector = self._generate_vector(echo_data.content) # Example
        # result_uuid = self.client.data_object.create(properties, ECHO_CLASS_NAME, vector=vector)

        try:
            result_uuid = self.client.data_object.create(
                data_object=properties,
                class_name=ECHO_CLASS_NAME
                # If providing vectors manually: vector=echo_data.vector
            )
            return Echo(id=result_uuid, **echo_data.model_dump())
        except Exception as e:
            print(f"Error adding Echo to Weaviate: {e}")
            raise

    async def get_echo(self, echo_id: str) -> Optional[Echo]:
        """Retrieves a specific Echo by its UUID from Weaviate."""
        if not self.client:
            raise ConnectionError("Weaviate client not connected.")
        try:
            data_object = self.client.data_object.get_by_id(
                uuid=echo_id,
                class_name=ECHO_CLASS_NAME
            )
            if data_object:
                props = data_object['properties']
                return Echo(
                    id=data_object['id'], # or echo_id
                    content=props.get('content'),
                    tags=props.get('tags', []),
                    created_at=props.get('created_at'), # Needs parsing from ISO string
                    updated_at=props.get('updated_at'), # Needs parsing
                    user_id=props.get('user_id'),
                    # metadata=... # Reconstruct metadata if needed
                )
            return None
        except Exception as e:
            print(f"Error getting Echo {echo_id} from Weaviate: {e}")
            return None # Or re-raise

    async def list_echos(self, filters: Optional[EchoFilter] = None, limit: int = 100, offset: int = 0) -> List[Echo]:
        """Lists Echos from Weaviate, optionally applying filters."""
        if not self.client:
            raise ConnectionError("Weaviate client not connected.")

        query_builder = self.client.query.get(ECHO_CLASS_NAME, ["content", "tags", "created_at", "updated_at", "user_id", "_additional{id}"]) \
                                   .with_limit(limit) \
                                   .with_offset(offset)

        # Basic filtering example (adapt to EchoFilter model)
        # This part needs to be more robust based on EchoFilter structure
        where_filter = None
        if filters:
            # Example: if filters.tags_include_all and filters.user_id:
            # where_filter = {
            #     "operator": "And",
            #     "operands": [
            #         {"path": ["user_id"], "operator": "Equal", "valueString": filters.user_id},
            #         # Add tag filtering - Weaviate's 'ContainsAll' is for list of strings
            #     ]
            # }
            # if where_filter:
            #    query_builder = query_builder.with_where(where_filter)
            print(f"Filtering not fully implemented for WeaviateStore. Filters received: {filters}")


        try:
            results = query_builder.do()
            echos = []
            for item in results['data']['Get'][ECHO_CLASS_NAME]:
                props = item # Weaviate v4 returns properties directly
                echos.append(Echo(
                    id=item['_additional']['id'],
                    content=props.get('content'),
                    tags=props.get('tags', []),
                    created_at=props.get('created_at'), # Needs parsing
                    updated_at=props.get('updated_at'), # Needs parsing
                    user_id=props.get('user_id'),
                ))
            return echos
        except Exception as e:
            print(f"Error listing Echos from Weaviate: {e}")
            return []

    async def update_echo(self, echo_id: str, echo_update_data: Dict[str, Any]) -> Optional[Echo]:
        """Updates an existing Echo in Weaviate."""
        if not self.client:
            raise ConnectionError("Weaviate client not connected.")
        try:
            # Weaviate's update replaces the object, merge updates properties.
            # For partial updates, use .data_object.update() or .data_object.merge()
            self.client.data_object.update(
                uuid=echo_id,
                class_name=ECHO_CLASS_NAME,
                data_object=echo_update_data
                # vector=new_vector if content changed and providing vectors manually
            )
            # Refetch the object to return the updated state
            return await self.get_echo(echo_id)
        except Exception as e:
            print(f"Error updating Echo {echo_id} in Weaviate: {e}")
            return None


    async def delete_echo(self, echo_id: str) -> bool:
        """Deletes an Echo from Weaviate."""
        if not self.client:
            raise ConnectionError("Weaviate client not connected.")
        try:
            self.client.data_object.delete(
                uuid=echo_id,
                class_name=ECHO_CLASS_NAME
            )
            return True
        except Exception as e:
            print(f"Error deleting Echo {echo_id} from Weaviate: {e}")
            return False

    async def search_echos_by_vector(self, vector: List[float], limit: int = 10, filters: Optional[EchoFilter] = None) -> List[Echo]:
        """Searches Echos by vector similarity."""
        if not self.client:
            raise ConnectionError("Weaviate client not connected.")

        near_vector = {"vector": vector}
        query_builder = self.client.query.get(ECHO_CLASS_NAME, ["content", "tags", "_additional{id, distance}"]) \
                                   .with_near_vector(near_vector) \
                                   .with_limit(limit)
        # Add filter support here if needed, similar to list_echos
        if filters:
            print(f"Filtering for vector search not fully implemented. Filters: {filters}")


        try:
            results = query_builder.do()
            echos = []
            for item in results['data']['Get'][ECHO_CLASS_NAME]:
                # props = item # v4
                echos.append(Echo(
                    id=item['_additional']['id'],
                    content=item.get('content'),
                    tags=item.get('tags', []),
                    # created_at, updated_at, user_id would also be here if requested in query
                    # vector_distance=item['_additional']['distance'] # Optionally include distance
                ))
            return echos
        except Exception as e:
            print(f"Error searching Echos by vector in Weaviate: {e}")
            return []


    async def search_echos_by_text(self, query_text: str, limit: int = 10, filters: Optional[EchoFilter] = None) -> List[Echo]:
        """Searches Echos by text similarity (hybrid or keyword)."""
        if not self.client:
            raise ConnectionError("Weaviate client not connected.")

        # Using Weaviate's bm25 search
        # For hybrid, you might use .with_hybrid() if configured
        query_builder = self.client.query.get(ECHO_CLASS_NAME, ["content", "tags", "_additional{id, score}"]) \
                                   .with_bm25(query=query_text, properties=["content^2", "tags"]) \
                                   .with_limit(limit)

        # Add filter support here if needed
        if filters:
            print(f"Filtering for text search not fully implemented. Filters: {filters}")

        try:
            results = query_builder.do()
            echos = []
            for item in results['data']['Get'][ECHO_CLASS_NAME]:
                # props = item # v4
                echos.append(Echo(
                    id=item['_additional']['id'],
                    content=item.get('content'),
                    tags=item.get('tags', []),
                    # search_score=item['_additional']['score'] # Optionally include score
                ))
            return echos
        except Exception as e:
            print(f"Error searching Echos by text in Weaviate: {e}")
            return []

# Example of how to use (for testing, typically called from a service layer)
async def _weaviate_example():
    store = WeaviateStore()
    try:
        await store.connect()
        # Ensure schema
        # await store.ensure_schema() # connect calls this

        # Add an Echo
        from datetime import datetime, timezone
        new_echo_data = EchoCreate(
            content="This is a test Echo from WeaviateStore example!",
            tags=["test", "weaviate"],
            user_id="user123",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        created_echo = await store.add_echo(new_echo_data)
        print(f"Created Echo: {created_echo}")

        if created_echo:
            # Get the Echo
            retrieved_echo = await store.get_echo(created_echo.id)
            print(f"Retrieved Echo: {retrieved_echo}")

            # List Echos
            all_echos = await store.list_echos(limit=5)
            print(f"Listed Echos: {all_echos}")

            # Search Echos (requires a vector or text if using text2vec module)
            # If Weaviate generates vectors, you might not need to provide one explicitly for text search
            # search_results_text = await store.search_echos_by_text("test Echo", limit=2)
            # print(f"Search results (text): {search_results_text}")

            # Delete Echo
            # deleted = await store.delete_echo(created_echo.id)
            # print(f"Echo deleted: {deleted}")

    except Exception as e:
        print(f"An error occurred in Weaviate example: {e}")
    finally:
        await store.disconnect()

if __name__ == "__main__":
    # import asyncio
    # asyncio.run(_weaviate_example()) # Commented out
    pass
