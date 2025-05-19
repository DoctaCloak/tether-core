from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from .models import Echo, EchoCreate, EchoFilter # Assuming models.py is in the same directory

class VectorStoreInterface(ABC):
    """
    Abstract Base Class defining the interface for vector store operations.
    This allows for interchangeable backend vector databases (Weaviate, Chroma, etc.).
    """

    @abstractmethod
    async def connect(self):
        """Connect to the vector store."""
        pass

    @abstractmethod
    async def disconnect(self):
        """Disconnect from the vector store."""
        pass

    @abstractmethod
    async def add_echo(self, echo_data: EchoCreate) -> Echo:
        """
        Adds a new Echo to the vector store.

        Args:
            echo_data (EchoCreate): The data for the new Echo.

        Returns:
            Echo: The created Echo, including its unique ID from the store.
        """
        pass

    @abstractmethod
    async def get_echo(self, echo_id: str) -> Optional[Echo]:
        """
        Retrieves a specific Echo by its ID.

        Args:
            echo_id (str): The unique ID of the Echo.

        Returns:
            Optional[Echo]: The Echo if found, otherwise None.
        """
        pass

    @abstractmethod
    async def list_echos(self, filters: Optional[EchoFilter] = None, limit: int = 100, offset: int = 0) -> List[Echo]:
        """
        Lists Echos, optionally applying filters, with pagination.

        Args:
            filters (Optional[EchoFilter]): Filters to apply (e.g., by tags, date range).
            limit (int): Maximum number of Echos to return.
            offset (int): Number of Echos to skip (for pagination).

        Returns:
            List[Echo]: A list of Echos.
        """
        pass

    @abstractmethod
    async def update_echo(self, echo_id: str, echo_update_data: Dict[str, Any]) -> Optional[Echo]:
        """
        Updates an existing Echo.

        Args:
            echo_id (str): The ID of the Echo to update.
            echo_update_data (Dict[str, Any]): A dictionary containing the fields to update.

        Returns:
            Optional[Echo]: The updated Echo if found and updated, otherwise None.
        """
        pass

    @abstractmethod
    async def delete_echo(self, echo_id: str) -> bool:
        """
        Deletes an Echo from the vector store.

        Args:
            echo_id (str): The ID of the Echo to delete.

        Returns:
            bool: True if deletion was successful, False otherwise.
        """
        pass

    @abstractmethod
    async def search_echos_by_vector(self, vector: List[float], limit: int = 10, filters: Optional[EchoFilter] = None) -> List[Echo]:
        """
        Searches for Echos based on vector similarity.

        Args:
            vector (List[float]): The query vector.
            limit (int): Maximum number of similar Echos to return.
            filters (Optional[EchoFilter]): Additional filters to apply to the search.


        Returns:
            List[Echo]: A list of similar Echos.
        """
        pass

    @abstractmethod
    async def search_echos_by_text(self, query_text: str, limit: int = 10, filters: Optional[EchoFilter] = None) -> List[Echo]:
        """
        Searches for Echos based on text similarity (hybrid search or BM25 + vector).

        Args:
            query_text (str): The query text.
            limit (int): Maximum number of similar Echos to return.
            filters (Optional[EchoFilter]): Additional filters to apply to the search.

        Returns:
            List[Echo]: A list of relevant Echos.
        """
        pass

    @abstractmethod
    async def ensure_schema(self):
        """
        Ensures that the necessary schema (e.g., 'Echo' class/collection) exists in the vector store.
        Creates it if it doesn't exist.
        """
        pass
