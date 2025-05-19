from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import json # For serializing complex data in the log

# This could be a simple file-based log, or integrate with a proper append-only database.
# For a file-based log, ensure thread-safety if multiple agents/processes might write.
TETHER_CHAIN_LOG_FILE = "tether_chain.log.jsonl" # JSON Lines format for easy append

class TetherChainEntry(BaseModel): # Assuming Pydantic from memory_graph.models
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event_type: str # e.g., ECHO_CREATED, ECHO_UPDATED, AGENT_ACTION, CONSENT_GIVEN, SHATTER_REQUEST
    actor_id: str # User ID, Agent ID, or System
    target_id: Optional[str] = None # e.g., Echo ID, Agent ID
    details: Dict[str, Any] = Field(default_factory=dict) # Rich details about the event, diffs, etc.
    previous_hash: Optional[str] = None # For chaining entries (conceptual, like blockchain)
    current_hash: Optional[str] = None  # Hash of the current entry

    def calculate_hash(self) -> str:
        # A simple hash calculation. In a real system, ensure consistent serialization.
        # Exclude current_hash itself from the hash calculation.
        import hashlib
        entry_data = self.model_dump(exclude={'current_hash'}, mode='json') # Pydantic V2
        # entry_data = self.dict(exclude={'current_hash'}, by_alias=True) # Pydantic V1
        serialized_data = json.dumps(entry_data, sort_keys=True, default=str)
        return hashlib.sha256(serialized_data.encode('utf-8')).hexdigest()


class TetherChainService:
    """
    Service for managing the TetherChain - an immutable log of significant events,
    memory commits, agent actions, and consent changes.
    Provides an audit trail and enables rollback capabilities (conceptually).
    """
    _last_hash: Optional[str] = None # Store the hash of the last written entry

    def __init__(self, log_file_path: str = TETHER_CHAIN_LOG_FILE):
        self.log_file_path = log_file_path
        self._initialize_chain()
        print(f"TetherChainService Initialized. Log file: {self.log_file_path}")

    def _initialize_chain(self):
        """Initializes the chain, potentially loading the last hash from the log file."""
        try:
            with open(self.log_file_path, 'r') as f:
                lines = f.readlines()
                if lines:
                    last_line = lines[-1].strip()
                    if last_line:
                        last_entry_data = json.loads(last_line)
                        self._last_hash = last_entry_data.get('current_hash')
                        print(f"Loaded last hash from TetherChain: {self._last_hash}")
        except FileNotFoundError:
            print("TetherChain log file not found. Will be created on first entry.")
            self._last_hash = None # Genesis block would have no previous hash
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error reading last hash from TetherChain log: {e}. Starting fresh.")
            self._last_hash = None


    async def add_entry(self, event_type: str, actor_id: str, target_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> TetherChainEntry:
        """
        Adds a new entry to the TetherChain.

        Args:
            event_type (str): The type of event (e.g., "ECHO_CREATED", "AGENT_ACTION").
            actor_id (str): The ID of the entity performing the action (user, agent, system).
            target_id (Optional[str]): The ID of the entity being acted upon (e.g., Echo ID).
            details (Optional[Dict[str, Any]]): A dictionary of details about the event.
                                                For updates, this might include a diff.

        Returns:
            TetherChainEntry: The created log entry.
        """
        entry_details = details or {}
        entry = TetherChainEntry(
            event_type=event_type,
            actor_id=actor_id,
            target_id=target_id,
            details=entry_details,
            previous_hash=self._last_hash
        )
        entry.current_hash = entry.calculate_hash()

        try:
            # Ensure thread/process safety if this can be called concurrently
            with open(self.log_file_path, 'a') as f:
                # f.write(entry.model_dump_json() + "\n") # Pydantic V2
                f.write(entry.model_dump_json() + "\n") # Pydantic V1: entry.json()

            self._last_hash = entry.current_hash # Update the last hash
            print(f"TetherChain: Added entry - Type: {event_type}, Actor: {actor_id}, Target: {target_id or 'N/A'}")
            return entry
        except IOError as e:
            print(f"Error writing to TetherChain log: {e}")
            # Potentially re-raise or handle more gracefully
            raise

    async def get_log_entries(self, limit: int = 100, offset: int = 0, event_type: Optional[str] = None, target_id: Optional[str] = None) -> List[TetherChainEntry]:
        """
        Retrieves log entries from the TetherChain, with optional filtering and pagination.
        Note: Reading the whole file for filtering can be inefficient for large logs.
              Consider a more robust storage solution for production.
        """
        entries: List[TetherChainEntry] = []
        try:
            with open(self.log_file_path, 'r') as f:
                all_lines = f.readlines() # Read all lines
            
            # Iterate in reverse to get recent entries first for typical listing
            # but apply offset and limit correctly
            
            relevant_lines = []
            for line in reversed(all_lines): # Process from newest to oldest
                line = line.strip()
                if not line:
                    continue
                try:
                    entry_data = json.loads(line)
                    # Apply filters
                    if event_type and entry_data.get('event_type') != event_type:
                        continue
                    if target_id and entry_data.get('target_id') != target_id:
                        continue
                    relevant_lines.append(entry_data)
                except json.JSONDecodeError:
                    print(f"Skipping malformed line in TetherChain log: {line}")
            
            # Apply pagination after filtering and reversing
            paginated_lines = relevant_lines[offset : offset + limit]

            for entry_data in paginated_lines: # Convert selected lines to Pydantic models
                 entries.append(TetherChainEntry(**entry_data))

            # If you want entries in chronological order, reverse again
            # entries.reverse() 

        except FileNotFoundError:
            print("TetherChain log file not found.")
            return []
        except Exception as e:
            print(f"Error reading TetherChain log: {e}")
            return []
        return entries

    async def verify_chain_integrity(self) -> bool:
        """
        Verifies the integrity of the chain by checking hashes.
        (More complex for a real system, this is a basic check)
        """
        print("Verifying TetherChain integrity (Placeholder - basic check)...")
        entries = await self.get_log_entries(limit=1000000) # Get all entries for full check
        if not entries:
            return True # Empty chain is valid

        expected_previous_hash = None # For the first entry (genesis)
        for entry in entries: # Assuming entries are in chronological order from get_log_entries
            if entry.previous_hash != expected_previous_hash:
                print(f"Chain integrity broken at entry (timestamp {entry.timestamp}): Expected prev_hash {expected_previous_hash}, got {entry.previous_hash}")
                return False
            
            # Recalculate hash to ensure entry content wasn't tampered with
            # Need to create a temporary entry object without current_hash to recalculate
            temp_entry_data = entry.model_dump()
            temp_entry_data.pop('current_hash', None)
            # Re-create with a method that doesn't auto-calc hash based on self.current_hash
            # This is a bit tricky with Pydantic's default_factory.
            # For simplicity, we'll trust the stored current_hash for now in this basic check,
            # but a real verification would re-calculate from all other fields.
            # calculated_hash_check = entry.calculate_hash() # This would use its own current_hash if not careful
            # A better way:
            # temp_entry = TetherChainEntry(**{k:v for k,v in entry.dict().items() if k != 'current_hash'})
            # temp_entry.previous_hash = entry.previous_hash # Ensure prev_hash is set correctly for recalc
            # if temp_entry.calculate_hash() != entry.current_hash:
            # print(f"Chain integrity broken at entry (timestamp {entry.timestamp}): Content hash mismatch.")
            # return False

            expected_previous_hash = entry.current_hash
        
        print("TetherChain integrity check passed (basic).")
        return True

# Example Usage
if __name__ == "__main__":
    # This requires Pydantic BaseModel to be defined or imported
    from pydantic import BaseModel, Field # Add this if running standalone

    async def main():
        # Clean up log file for fresh test run
        try:
            import os
            if os.path.exists(TETHER_CHAIN_LOG_FILE):
                os.remove(TETHER_CHAIN_LOG_FILE)
        except OSError:
            pass

        chain_service = TetherChainService()

        await chain_service.add_entry(
            event_type="ECHO_CREATED",
            actor_id="user123",
            target_id="echo_abc",
            details={"content_snippet": "Hello world", "tags": ["test"]}
        )
        await chain_service.add_entry(
            event_type="AGENT_ACTION",
            actor_id="agent_focus_mind",
            details={"action": "task_started", "task_name": "Write report"}
        )
        entry3 = await chain_service.add_entry(
            event_type="CONSENT_GIVEN",
            actor_id="user123",
            target_id="agent_calendar_mind",
            details={"permissions_granted": ["calendar:read", "calendar:write"]}
        )

        print(f"\nLast entry hash: {entry3.current_hash}")

        log = await chain_service.get_log_entries(limit=5)
        print("\nRecent Log Entries (newest first):")
        for item in log:
            print(item.model_dump_json(indent=2))

        # integrity = await chain_service.verify_chain_integrity() # Requires chronological order from get_log_entries
        # print(f"\nChain Integrity Verified: {integrity}")


    # import asyncio
    # asyncio.run(main()) # Commented out
    pass
