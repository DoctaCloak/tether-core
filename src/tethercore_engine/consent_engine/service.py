from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

# from ..tether_chain.service import TetherChainService # For logging consent changes

class PermissionRequest(BaseModel):
    """Represents a request for permission by an agent or service."""
    requester_id: str # e.g., agent_id
    resource: str     # e.g., "calendar", "memory_graph:echo_tag_personal"
    actions: List[str]  # e.g., ["read", "write"]
    justification: Optional[str] = None # Why the permission is needed
    # expires_at: Optional[datetime] = None # Optional expiry for the permission

class ConsentRecord(BaseModel):
    """Represents a record of user consent."""
    user_id: str
    requester_id: str
    resource: str
    actions_granted: List[str]
    actions_denied: Optional[List[str]] = Field(default_factory=list)
    granted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    # expires_at: Optional[datetime] = None
    status: str = "active" # e.g., "active", "revoked", "expired"
    conditions: Optional[Dict[str, Any]] = Field(default_factory=dict) # e.g. {"max_daily_access": 10}

class ConsentEngineService:
    """
    Service for managing user consent for agent actions and data access.
    It interfaces with the Trust Contract Layer and logs consent changes to TetherChain.
    """
    # For simplicity, using an in-memory store. A real implementation needs persistent storage.
    _consent_db: Dict[str, List[ConsentRecord]] = {} # Key: user_id

    def __init__(self, tether_chain_service = None): # Pass TetherChainService instance
        # self.tether_chain = tether_chain_service
        print("ConsentEngineService Initialized (In-memory storage).")

    async def request_consent(self, user_id: str, permission_request: PermissionRequest) -> bool:
        """
        Presents a permission request to the user (simulated here).
        In a real system, this would trigger a UI notification or prompt.

        Returns:
            bool: True if consent is granted (simulated), False otherwise.
        """
        print(f"ConsentEngine: Requesting consent from user '{user_id}' for:")
        print(f"  Requester: {permission_request.requester_id}")
        print(f"  Resource:  {permission_request.resource}")
        print(f"  Actions:   {permission_request.actions}")
        print(f"  Justification: {permission_request.justification or 'N/A'}")

        # Simulate user interaction (e.g., from UI or CLI prompt)
        # For now, let's assume auto-approval for some resources for testing,
        # or a default denial. This needs proper user interaction.
        if "memory_graph" in permission_request.resource and "read" in permission_request.actions:
            print("ConsentEngine: Auto-simulating approval for read access to memory_graph.")
            await self.grant_consent(user_id, permission_request, permission_request.actions)
            return True
        
        print("ConsentEngine: Simulating user denial or no response for other requests.")
        await self.record_denial(user_id, permission_request, permission_request.actions)
        return False


    async def grant_consent(self, user_id: str, request: PermissionRequest, granted_actions: List[str], conditions: Optional[Dict[str, Any]] = None):
        """Records that a user has granted consent."""
        record = ConsentRecord(
            user_id=user_id,
            requester_id=request.requester_id,
            resource=request.resource,
            actions_granted=granted_actions,
            conditions=conditions or {}
        )
        if user_id not in self._consent_db:
            self._consent_db[user_id] = []
        
        # Remove any previous conflicting records or update existing ones (simplified)
        self._consent_db[user_id] = [
            r for r in self._consent_db[user_id]
            if not (r.requester_id == request.requester_id and r.resource == request.resource)
        ]
        self._consent_db[user_id].append(record)

        print(f"Consent granted by '{user_id}' to '{request.requester_id}' for '{request.resource}' actions: {granted_actions}")
        # if self.tether_chain:
        #     await self.tether_chain.add_entry(
        #         event_type="CONSENT_GRANTED",
        #         actor_id=user_id,
        #         target_id=request.requester_id,
        #         details={
        #             "resource": request.resource,
        #             "actions_granted": granted_actions,
        #             "conditions": record.conditions
        #         }
        #     )

    async def record_denial(self, user_id: str, request: PermissionRequest, denied_actions: List[str]):
        """Records that a user has denied consent (or it was not given)."""
        # This is a simplified denial logging. You might not store explicit denial records
        # in the same way as grants, or they might have a different status.
        print(f"Consent denied or not provided by '{user_id}' to '{request.requester_id}' for '{request.resource}' actions: {denied_actions}")
        # if self.tether_chain:
        #     await self.tether_chain.add_entry(
        #         event_type="CONSENT_DENIED",
        #         actor_id=user_id,
        #         target_id=request.requester_id,
        #         details={
        #             "resource": request.resource,
        #             "actions_denied": denied_actions,
        #             "justification": request.justification
        #         }
        #     )


    async def check_consent(self, user_id: str, requester_id: str, resource: str, action: str) -> bool:
        """
        Checks if a specific action is permitted for a requester on a resource by a user.
        """
        if user_id not in self._consent_db:
            return False
        
        for record in self._consent_db[user_id]:
            if record.requester_id == requester_id and \
               record.resource == resource and \
               action in record.actions_granted and \
               record.status == "active":
                # TODO: Check conditions and expiry if implemented
                # if record.expires_at and record.expires_at < datetime.now(timezone.utc):
                #     record.status = "expired" # Mark as expired
                #     # Log to TetherChain
                #     return False
                return True
        return False

    async def revoke_consent(self, user_id: str, requester_id: str, resource: str, actions: Optional[List[str]] = None):
        """Revokes consent for specific actions or all actions on a resource."""
        if user_id not in self._consent_db:
            print(f"No consent records found for user '{user_id}' to revoke.")
            return

        updated_records = []
        revoked_something = False
        for record in self._consent_db[user_id]:
            if record.requester_id == requester_id and record.resource == resource:
                if actions is None: # Revoke all actions for this resource/requester
                    record.status = "revoked"
                    revoked_something = True
                    print(f"All consent revoked for '{requester_id}' on '{resource}' by '{user_id}'.")
                    # Log to TetherChain
                else:
                    original_granted = set(record.actions_granted)
                    actions_to_revoke = set(actions)
                    record.actions_granted = list(original_granted - actions_to_revoke)
                    if not record.actions_granted: # If all actions removed, mark as revoked
                        record.status = "revoked"
                    revoked_something = True
                    print(f"Consent for actions {actions_to_revoke} revoked for '{requester_id}' on '{resource}' by '{user_id}'.")
                    # Log to TetherChain
            if record.status == "active": # Keep only active or non-matching records
                 updated_records.append(record)
        
        self._consent_db[user_id] = updated_records
        if not revoked_something:
            print(f"No matching active consent found to revoke for '{requester_id}' on '{resource}'.")


    async def get_user_consents(self, user_id: str) -> List[ConsentRecord]:
        """Retrieves all active consent records for a user."""
        return [r for r in self._consent_db.get(user_id, []) if r.status == "active"]

# Example Usage
if __name__ == "__main__":
    async def main():
        consent_service = ConsentEngineService()
        user_id = "user_test_consent"
        agent_id_focus = "agent_focus_mind"
        agent_id_calendar = "agent_calendar_mind"

        # Agent requests permission
        perm_req_focus_read_mem = PermissionRequest(
            requester_id=agent_id_focus,
            resource="memory_graph",
            actions=["read"],
            justification="FocusMind needs to read past focus sessions to provide insights."
        )
        perm_req_calendar_write = PermissionRequest(
            requester_id=agent_id_calendar,
            resource="calendar_api",
            actions=["write_event", "read_event"],
            justification="CalendarMind needs to create and read events on your behalf."
        )

        # Simulate user granting/denying (request_consent simulates this)
        await consent_service.request_consent(user_id, perm_req_focus_read_mem) # Simulates auto-approval
        await consent_service.request_consent(user_id, perm_req_calendar_write) # Simulates denial

        # Check specific consent
        can_focus_read = await consent_service.check_consent(user_id, agent_id_focus, "memory_graph", "read")
        print(f"Can FocusMind read memory_graph? {can_focus_read}")

        can_calendar_write = await consent_service.check_consent(user_id, agent_id_calendar, "calendar_api", "write_event")
        print(f"Can CalendarMind write to calendar_api? {can_calendar_write}")

        # Grant calendar write explicitly for testing check
        await consent_service.grant_consent(user_id, perm_req_calendar_write, ["write_event", "read_event"])
        can_calendar_write_after_grant = await consent_service.check_consent(user_id, agent_id_calendar, "calendar_api", "write_event")
        print(f"Can CalendarMind write to calendar_api after explicit grant? {can_calendar_write_after_grant}")


        # List consents
        consents = await consent_service.get_user_consents(user_id)
        print(f"\nActive consents for {user_id}:")
        for c in consents:
            print(c.model_dump_json(indent=2))

        # Revoke consent
        await consent_service.revoke_consent(user_id, agent_id_calendar, "calendar_api", ["write_event"])
        can_calendar_write_after_revoke = await consent_service.check_consent(user_id, agent_id_calendar, "calendar_api", "write_event")
        print(f"Can CalendarMind write to calendar_api after revoking 'write_event'? {can_calendar_write_after_revoke}")
        can_calendar_read_after_revoke = await consent_service.check_consent(user_id, agent_id_calendar, "calendar_api", "read_event")
        print(f"Can CalendarMind read calendar_api after revoking 'write_event'? {can_calendar_read_after_revoke}")


    # import asyncio
    # asyncio.run(main()) # Commented out
    pass
