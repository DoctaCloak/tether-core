from ...base_agent import BaseAgent, AgentContext # Relative import
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

class CalendarMindAgent(BaseAgent):
    """
    CalendarMind Agent: Manages calendar events, schedules, and reminders.
    This is a very basic placeholder. Real calendar integration is complex.
    """

    async def setup(self, config: Optional[Dict[str, Any]] = None):
        await super().setup(config)
        # In a real agent, this might connect to a calendar API (Google Calendar, Outlook, etc.)
        # using credentials/tokens provided securely through context or config.
        self.events: List[Dict[str, Any]] = [] # Simple in-memory store for events
        print(f"CalendarMindAgent '{self.agent_id}': Setup complete. Ready to manage calendar events (in-memory).")

    async def execute_task(self, task_description: str, task_parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        await super().execute_task(task_description, task_parameters)
        task_parameters = task_parameters or {}
        
        # Example: "add event 'Team Meeting' tomorrow at 10am for 1 hour"
        # Example: "what's on my calendar today?"
        # Example: "find free time next week for a 30 minute call"

        if "add event" in task_description.lower():
            # Extremely simplified parsing. NLU/LLM would be needed for robust parsing.
            try:
                # Example: "add event 'My Event' on 2025-12-25 from 10:00 to 11:00"
                event_name = task_parameters.get("name", "Unnamed Event")
                start_time_str = task_parameters.get("start_time") # Expects ISO format string
                end_time_str = task_parameters.get("end_time")     # Expects ISO format string
                
                if not start_time_str or not event_name:
                    return {"status": "error", "message": "Event name and start_time are required to add an event."}

                start_time = datetime.fromisoformat(start_time_str)
                end_time = datetime.fromisoformat(end_time_str) if end_time_str else start_time + timedelta(hours=1)

                new_event = {
                    "id": str(len(self.events) + 1), # Simple ID
                    "summary": event_name,
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat(),
                    "description": task_parameters.get("description", "")
                }
                self.events.append(new_event)
                await self.context.log_to_tether_chain(
                    event_type="CALENDAR_EVENT_ADDED",
                    details={"event_summary": event_name, "start_time": start_time.isoformat()},
                )
                await self._save_to_memory_graph(
                    content=f"Added calendar event: {event_name} starting at {start_time.strftime('%Y-%m-%d %H:%M')}",
                    tags=["calendar", "event_added", event_name.replace(" ", "_")]
                )
                return {"status": "success", "message": f"Event '{event_name}' added.", "event_id": new_event["id"]}
            except Exception as e:
                return {"status": "error", "message": f"Failed to add event: {e}"}

        elif "what's on my calendar" in task_description.lower() or "list events" in task_description.lower():
            # Simplified: list all events or filter by a date (if provided)
            date_filter_str = task_parameters.get("date") # e.g., "today", "tomorrow", "2025-12-25"
            
            display_events = []
            if not self.events:
                 return {"status": "success", "message": "Your calendar is empty.", "events": []}

            for event in self.events:
                # Basic date filtering placeholder
                # A real implementation would parse date_filter_str and compare event start/end times
                display_events.append(event)
            
            return {"status": "success", "events": display_events}

        else:
            llm_response = await self._get_llm_response(
                f"As CalendarMind, how should I handle: '{task_description}'? Params: {task_parameters}"
            )
            return {"status": "info", "message": "Calendar task not specifically handled, providing general LLM response.", "llm_suggestion": llm_response}

# Example for standalone testing
if __name__ == "__main__":
    async def _calendar_mind_test():
        print("Running CalendarMindAgent standalone test (limited context)...")
        ctx = AgentContext(agent_id="calendar_mind_test_001", user_id="test_user")
        agent = CalendarMindAgent(context=ctx)
        await agent.setup()

        # Add an event
        event_params_add = {
            "name": "Team Standup",
            "start_time": (datetime.now() + timedelta(days=1, hours=2)).isoformat(), # Tomorrow +2 hours
            "end_time": (datetime.now() + timedelta(days=1, hours=2, minutes=30)).isoformat(),
            "description": "Daily team sync"
        }
        result_add = await agent.execute_task("Add event", event_params_add)
        print(f"Add Event Result: {result_add}")
        
        event_params_add2 = {
            "name": "Project Planning",
            "start_time": (datetime.now() + timedelta(days=2, hours=4)).isoformat(),
        }
        result_add2 = await agent.execute_task("Add event 'Project Planning'", event_params_add2) # Name in desc
        print(f"Add Event 2 Result: {result_add2}")


        # List events
        result_list = await agent.execute_task("What's on my calendar?")
        print(f"List Events Result: {result_list}")

    # import asyncio
    # asyncio.run(_calendar_mind_test()) # Commented out
    pass
