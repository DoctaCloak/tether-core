from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

# Potentially import service interfaces if agents interact directly
# from ..memory_graph.store_interface import VectorStoreInterface
# from ..llm_router.service import LLMRouterService
# from ..tether_chain.service import TetherChainService
# from ..agent_runtime.manifest_parser import AgentManifest # For agent's own manifest

class AgentContext:
    """
    Provides context to the agent during its execution.
    This might include access to TetherCore services, configuration, user info, etc.
    """
    def __init__(
        self,
        agent_id: str,
        user_id: str,
        # memory_graph: Optional[VectorStoreInterface] = None,
        # llm_router: Optional[LLMRouterService] = None,
        # tether_chain: Optional[TetherChainService] = None,
        agent_manifest: Optional[Dict[str, Any]] = None, # Could be the parsed AgentManifest model
        agent_custom_config: Optional[Dict[str, Any]] = None
    ):
        self.agent_id = agent_id
        self.user_id = user_id
        # self.memory_graph = memory_graph
        # self.llm_router = llm_router
        # self.tether_chain = tether_chain
        self.agent_manifest = agent_manifest or {}
        self.agent_custom_config = agent_custom_config or {}
        print(f"AgentContext created for agent: {agent_id}, user: {user_id}")

    async def log_to_tether_chain(self, event_type: str, details: Dict[str, Any], target_id: Optional[str] = None):
        """Helper method to log agent actions to TetherChain."""
        print(f"Agent '{self.agent_id}' logging to TetherChain: Event '{event_type}', Target '{target_id or 'N/A'}'")
        # if self.tether_chain:
        #     await self.tether_chain.add_entry(
        #         event_type=event_type,
        #         actor_id=self.agent_id, # Agent itself is the actor
        #         target_id=target_id,
        #         details=details
        #     )
        # else:
        #     print("Warning: TetherChain service not available in AgentContext for logging.")
        pass # Placeholder

class BaseAgent(ABC):
    """
    Abstract Base Class for all Mindscape Agents.
    Defines the common interface and lifecycle methods for agents.
    """
    manifest: Optional[Dict[str, Any]] = None # Store parsed manifest if needed

    def __init__(self, context: AgentContext):
        """
        Initialize the agent with its context.
        The context provides access to necessary TetherCore services and configuration.
        """
        self.context = context
        self.agent_id = context.agent_id
        self.user_id = context.user_id
        print(f"BaseAgent (ID: {self.agent_id}) initialized for user: {self.user_id}.")

    @abstractmethod
    async def setup(self, config: Optional[Dict[str, Any]] = None):
        """
        Called once when the agent is being set up or deployed.
        Use this to initialize resources, load models, etc.
        Args:
            config (Optional[Dict[str, Any]]): Agent-specific configuration.
        """
        print(f"Agent '{self.agent_id}': Setup method called.")
        pass

    @abstractmethod
    async def execute_task(self, task_description: str, task_parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        The main method called to execute a task.

        Args:
            task_description (str): A natural language description of the task.
            task_parameters (Optional[Dict[str, Any]]): Structured parameters for the task,
                                                       potentially conforming to an input schema.

        Returns:
            Dict[str, Any]: A dictionary containing the result of the task execution,
                            which might include status, output data, and any errors.
                            Should ideally conform to an output schema.
        """
        print(f"Agent '{self.agent_id}': Executing task '{task_description}' with params: {task_parameters}")
        pass

    async def on_heartbeat(self):
        """
        Optional: Called periodically if the agent runtime supports heartbeats for long-running agents.
        Can be used for periodic checks, updates, or cleanup.
        """
        print(f"Agent '{self.agent_id}': Heartbeat received (placeholder).")
        pass

    async def on_shutdown(self):
        """
        Optional: Called when the agent is being shut down.
        Use this to release resources, save state, etc.
        """
        print(f"Agent '{self.agent_id}': Shutdown method called.")
        pass

    # Helper methods agents might use (examples)
    async def _get_llm_response(self, prompt: str, preferred_models: Optional[List[str]]=None) -> Optional[str]:
        """Helper to interact with the LLM router via context."""
        print(f"Agent '{self.agent_id}': Requesting LLM response for prompt: '{prompt[:30]}...'")
        # if self.context.llm_router:
        #     models_to_try = preferred_models or self.context.agent_manifest.get("llm_config", {}).get("preferred_models", [])
        #     # Basic logic to try preferred models
        #     if models_to_try:
        #         for model in models_to_try:
        #             try:
        #                 return await self.context.llm_router.query(prompt, model=model)
        #             except Exception as e:
        #                 print(f"Agent '{self.agent_id}': Failed to get response from {model}: {e}")
        #     # Fallback to default if preferred models fail or none specified
        #     return await self.context.llm_router.query(prompt)
        # else:
        #     print(f"Agent '{self.agent_id}': LLM Router not available in context.")
        #     return None
        return f"Placeholder LLM response to: {prompt}"

    async def _save_to_memory_graph(self, content: str, tags: Optional[List[str]] = None, metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Helper to save an Echo to the memory graph via context."""
        from ..memory_graph.models import EchoCreate # Local import to avoid circularity if services use agents
        
        print(f"Agent '{self.agent_id}': Saving to memory graph. Content: '{content[:30]}...' Tags: {tags}")
        # if self.context.memory_graph:
        #     echo_data = EchoCreate(
        #         content=content,
        #         tags=tags or [],
        #         user_id=self.user_id,
        #         metadata=metadata or {"agent_source": self.agent_id}
        #     )
        #     created_echo = await self.context.memory_graph.add_echo(echo_data)
        #     if created_echo:
        #         await self.context.log_to_tether_chain(
        #             event_type="AGENT_ECHO_CREATED",
        #             details={"echo_content_snippet": content[:50], "tags": tags},
        #             target_id=created_echo.id
        #         )
        #         return created_echo.id
        # else:
        #     print(f"Agent '{self.agent_id}': Memory Graph not available in context.")
        #     return None
        return "mock_echo_id_from_agent"

if __name__ == "__main__":
    # Example of how a concrete agent might be structured (won't run directly without context)
    class MyTestAgent(BaseAgent):
        async def setup(self, config: Optional[Dict[str, Any]] = None):
            await super().setup(config) # Call base method
            print(f"MyTestAgent '{self.agent_id}': Custom setup complete. Config: {config}")
            # Load specific resources for MyTestAgent

        async def execute_task(self, task_description: str, task_parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
            await super().execute_task(task_description, task_parameters) # Call base method
            print(f"MyTestAgent '{self.agent_id}': Executing task - {task_description}")
            
            # Example: Use LLM
            llm_prompt = f"Based on the task '{task_description}', what should be the next step?"
            llm_response = await self._get_llm_response(llm_prompt)
            print(f"MyTestAgent LLM Response: {llm_response}")

            # Example: Save to memory
            memory_content = f"Task '{task_description}' processed. LLM suggested: {llm_response}"
            echo_id = await self._save_to_memory_graph(memory_content, tags=["test_agent_task", "llm_interaction"])
            
            return {"status": "success", "message": "Task processed by MyTestAgent", "llm_suggestion": llm_response, "echo_id": echo_id}

    # To run this, you'd need to instantiate AgentContext and then MyTestAgent.
    # This is just for structural illustration.
    # async def demo():
    #     ctx = AgentContext(agent_id="my_test_agent_001", user_id="user_abc")
    #     agent = MyTestAgent(context=ctx)
    #     await agent.setup(config={"custom_param": 123})
    #     result = await agent.execute_task("Summarize recent activities", {"period": "last_day"})
    #     print(f"Demo Agent Task Result: {result}")
    # import asyncio
    # asyncio.run(demo())
    pass
