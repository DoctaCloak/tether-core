from ...base_agent import BaseAgent, AgentContext # Relative import from parent package
from typing import Dict, Any, Optional, List

class FocusMindAgent(BaseAgent):
    """
    FocusMind Agent: Helps manage focus sessions, tasks, and minimize distractions.
    """

    async def setup(self, config: Optional[Dict[str, Any]] = None):
        """Initialize FocusMind specific resources or settings."""
        await super().setup(config) # Important to call base setup
        self.current_focus_task: Optional[str] = None
        self.focus_duration_minutes: int = self.context.agent_custom_config.get("default_focus_duration_minutes", 25)
        print(f"FocusMindAgent '{self.agent_id}': Setup complete. Default focus duration: {self.focus_duration_minutes} mins.")

    async def execute_task(self, task_description: str, task_parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Executes a focus-related task.
        Examples: "start focus session on 'writing report'", "get current focus task", "suggest break activity"
        """
        await super().execute_task(task_description, task_parameters)
        task_parameters = task_parameters or {}
        
        # Simple command parsing based on task_description
        # A more robust agent would use NLU or structured commands
        if "start focus session on" in task_description.lower():
            # Extract task name, e.g., "start focus session on 'Project X planning'"
            try:
                self.current_focus_task = task_description.lower().split("start focus session on", 1)[1].strip().strip("'\"")
                duration = task_parameters.get("duration_minutes", self.focus_duration_minutes)
                
                await self.context.log_to_tether_chain(
                    event_type="FOCUS_SESSION_STARTED",
                    details={"task": self.current_focus_task, "duration_minutes": duration},
                )
                await self._save_to_memory_graph(
                    content=f"Started focus session on: {self.current_focus_task} for {duration} minutes.",
                    tags=["focus_session", "task_management", self.current_focus_task.replace(" ", "_")]
                )
                return {"status": "success", "message": f"Focus session started on '{self.current_focus_task}' for {duration} minutes."}
            except IndexError:
                 return {"status": "error", "message": "Could not parse task name from 'start focus session' command."}

        elif "get current focus task" in task_description.lower():
            if self.current_focus_task:
                return {"status": "success", "current_task": self.current_focus_task}
            else:
                return {"status": "success", "message": "No active focus task."}

        elif "suggest break activity" in task_description.lower():
            # Example LLM interaction
            prompt = "Suggest a short, refreshing break activity for someone working on a computer."
            suggestion = await self._get_llm_response(prompt)
            await self._save_to_memory_graph(
                content=f"Suggested break activity: {suggestion}",
                tags=["break_suggestion", "wellbeing"]
            )
            return {"status": "success", "suggestion": suggestion or "Take a short walk or stretch."}
            
        else:
            # Fallback to a general LLM query if task is not recognized
            llm_response = await self._get_llm_response(
                f"As a FocusMind agent, how should I respond to the request: '{task_description}'? Parameters: {task_parameters}"
            )
            return {"status": "info", "message": "Task not specifically handled, providing general LLM response.", "llm_suggestion": llm_response}

    async def on_shutdown(self):
        await super().on_shutdown()
        print(f"FocusMindAgent '{self.agent_id}': Shutting down. Current task was: {self.current_focus_task}")
        # Potentially save any pending state

# Example of how this agent might be run by the AgentRunnerService (conceptual)
# This would typically happen inside the Docker container for the agent.
if __name__ == "__main__":
    # This main block is for direct testing of the agent logic if needed,
    # but it won't have the full AgentContext provided by the runtime.
    async def _focus_mind_test():
        print("Running FocusMindAgent standalone test (limited context)...")
        # Mock context for basic testing
        mock_manifest = {
            "agent_id": "focus_mind_test_001",
            "custom_config": {"default_focus_duration_minutes": 5} # Short for testing
        }
        ctx = AgentContext(
            agent_id=mock_manifest["agent_id"],
            user_id="test_user",
            agent_manifest=mock_manifest,
            agent_custom_config=mock_manifest["custom_config"]
        )
        agent = FocusMindAgent(context=ctx)
        await agent.setup()

        result1 = await agent.execute_task("Start focus session on 'testing the agent'")
        print(f"Test Result 1: {result1}")

        result2 = await agent.execute_task("Get current focus task")
        print(f"Test Result 2: {result2}")

        result3 = await agent.execute_task("Suggest break activity")
        print(f"Test Result 3: {result3}")
        
        result4 = await agent.execute_task("What is the capital of Minnesota?") # Unhandled
        print(f"Test Result 4: {result4}")

        await agent.on_shutdown()

    # import asyncio
    # asyncio.run(_focus_mind_test()) # Commented out
    pass
