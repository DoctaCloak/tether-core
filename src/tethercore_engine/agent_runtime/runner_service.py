import docker # Docker SDK for Python
from docker.errors import NotFound, APIError
from typing import Dict, Any, Optional, List
from .manifest_parser import AgentManifest # Assuming manifest_parser.py is in the same directory

# Configuration
DOCKER_CLIENT_TIMEOUT = 120 # Seconds

class AgentRunnerService:
    """
    Service for running and managing Mindscape Agents in isolated environments (e.g., Docker containers).
    """
    client: Optional[docker.DockerClient] = None

    def __init__(self, docker_socket_url: Optional[str] = None):
        """
        Initializes the AgentRunnerService.
        Args:
            docker_socket_url (str, optional): URL for the Docker daemon socket.
                                               Defaults to system default if None.
        """
        try:
            if docker_socket_url:
                self.client = docker.DockerClient(base_url=docker_socket_url, timeout=DOCKER_CLIENT_TIMEOUT)
            else:
                self.client = docker.from_env(timeout=DOCKER_CLIENT_TIMEOUT)
            self.client.ping() # Check connection
            print("AgentRunnerService: Successfully connected to Docker daemon.")
        except APIError as e:
            print(f"AgentRunnerService: Failed to connect to Docker daemon: {e}")
            print("Please ensure Docker is running and accessible.")
            self.client = None # Ensure client is None if connection failed
        except Exception as e_gen:
            print(f"AgentRunnerService: An unexpected error occurred while connecting to Docker: {e_gen}")
            self.client = None


    async def deploy_agent(self, manifest: AgentManifest) -> Dict[str, Any]:
        """
        Deploys an agent based on its manifest.
        For Docker, this might involve pulling an image or building one if a Dockerfile is specified.
        For now, this is a placeholder as actual deployment is complex.

        Args:
            manifest (AgentManifest): The parsed agent manifest.

        Returns:
            Dict[str, Any]: Deployment status and information.
        """
        if not self.client:
            return {"status": "error", "message": "Docker client not available."}

        print(f"AgentRunnerService: Deploying agent '{manifest.agent_id}' (version {manifest.version})")
        print(f"  Image: {manifest.runtime.image if manifest.runtime else 'N/A'}")
        print(f"  Entrypoint: {manifest.runtime.entrypoint if manifest.runtime else 'N/A'}")

        # Placeholder: Actual image pulling/building logic would go here.
        # if manifest.runtime and manifest.runtime.image:
        #     try:
        #         print(f"Pulling image: {manifest.runtime.image}...")
        #         self.client.images.pull(manifest.runtime.image)
        #         print("Image pulled successfully.")
        #     except APIError as e:
        #         print(f"Error pulling image {manifest.runtime.image}: {e}")
        #         return {"status": "error", "message": f"Failed to pull image: {e}"}

        return {"status": "success", "agent_id": manifest.agent_id, "message": "Agent deployment initiated (placeholder)."}

    async def run_agent_task(self, agent_id: str, task_description: str, agent_config: Optional[Dict[str, Any]] = None, environment_vars: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Runs a task for a specified agent in a new container.

        Args:
            agent_id (str): The ID of the agent to run (should correspond to a deployed image/config).
            task_description (str): A description of the task for the agent.
            agent_config (Optional[Dict[str, Any]]): Specific configuration for this agent run,
                                                     potentially sourced from its manifest or user input.
            environment_vars (Optional[Dict[str, str]]): Environment variables to set for the container.

        Returns:
            Dict[str, Any]: Information about the task execution (e.g., container ID, logs).
        """
        if not self.client:
            return {"status": "error", "message": "Docker client not available."}

        print(f"AgentRunnerService: Running task for agent '{agent_id}': '{task_description}'")
        image_name = agent_config.get("runtime", {}).get("image") if agent_config else f"tether_agent_{agent_id}" # Example image name
        entrypoint_cmd = agent_config.get("runtime", {}).get("entrypoint", []) if agent_config else []
        
        if not image_name:
            return {"status": "error", "message": f"No image specified for agent '{agent_id}'."}

        # Command to pass to the container. This needs to be structured based on how the agent image expects tasks.
        # For example, it might be an argument to the entrypoint.
        command_to_run = entrypoint_cmd + [task_description] # Simplistic example

        env = environment_vars or {}
        env["TETHER_TASK_DESCRIPTION"] = task_description # Example of passing task via env var

        try:
            print(f"Attempting to run container from image: {image_name} with command: {command_to_run}")
            container = self.client.containers.run(
                image=image_name,
                command=command_to_run,
                environment=env,
                detach=True,  # Run in detached mode
                # network_mode="host", # Or a specific bridge network for controlled communication
                # volumes={...}, # If agents need persistent storage or access to host files (use with caution)
                # remove=True # Automatically remove container when it exits (for short-lived tasks)
            )
            print(f"Agent '{agent_id}' task started in container: {container.short_id}")
            return {"status": "success", "agent_id": agent_id, "container_id": container.short_id, "message": "Task started."}
        except NotFound:
            print(f"Error: Docker image '{image_name}' not found for agent '{agent_id}'.")
            return {"status": "error", "message": f"Image '{image_name}' not found."}
        except APIError as e:
            print(f"Error running agent '{agent_id}' container: {e}")
            return {"status": "error", "message": f"Docker API error: {e}"}
        except Exception as e_gen:
            print(f"An unexpected error occurred while running agent '{agent_id}': {e_gen}")
            return {"status": "error", "message": f"Unexpected error: {e_gen}"}


    async def get_agent_logs(self, container_id: str, tail: int = 100) -> Optional[str]:
        """
        Retrieves logs from a specific agent container.

        Args:
            container_id (str): The ID of the container.
            tail (int): The number of log lines to retrieve from the end.

        Returns:
            Optional[str]: The container logs as a string, or None if an error occurs.
        """
        if not self.client:
            print("Docker client not available.")
            return None
        try:
            container = self.client.containers.get(container_id)
            logs = container.logs(tail=tail, timestamps=True).decode('utf-8')
            return logs
        except NotFound:
            print(f"Error: Container '{container_id}' not found.")
            return None
        except APIError as e:
            print(f"Error retrieving logs for container '{container_id}': {e}")
            return None

    async def stop_agent_task(self, container_id: str) -> bool:
        """
        Stops a running agent task (container).

        Args:
            container_id (str): The ID of the container to stop.

        Returns:
            bool: True if stopping was successful or container already stopped, False otherwise.
        """
        if not self.client:
            print("Docker client not available.")
            return False
        try:
            container = self.client.containers.get(container_id)
            container.stop(timeout=10) # Wait up to 10 seconds for graceful stop
            # container.remove() # Optionally remove after stopping
            print(f"Stopped container: {container_id}")
            return True
        except NotFound:
            print(f"Warning: Container '{container_id}' not found for stopping (might have already exited).")
            return True # Consider it success if not found
        except APIError as e:
            print(f"Error stopping container '{container_id}': {e}")
            return False

    async def list_running_agents(self) -> List[Dict[str, Any]]:
        """Lists all currently running agent containers managed by this runtime (conceptually)."""
        if not self.client:
            return []
        
        running_agent_containers = []
        try:
            # This lists all containers; you might need specific labels to identify TetherCore agents
            for container in self.client.containers.list(filters={"status": "running"}):
                # Assuming TetherCore agents have a specific label, e.g., "tethercore.agent_id"
                agent_id = container.labels.get("tethercore.agent_id", "unknown")
                running_agent_containers.append({
                    "container_id": container.short_id,
                    "image": container.attrs['Config']['Image'],
                    "status": container.status,
                    "name": container.name,
                    "agent_id": agent_id # You'd need to set this label when running the container
                })
            return running_agent_containers
        except APIError as e:
            print(f"Error listing running agent containers: {e}")
            return []

# Example Usage
async def _agent_runner_example():
    runner = AgentRunnerService()
    if not runner.client:
        print("AgentRunnerService example cannot run without Docker client.")
        return

    # This example assumes you have a Docker image named 'hello-world-agent'
    # or an agent manifest that points to a valid image.
    # For a real test, you'd build a simple agent Docker image.

    # 1. (Conceptual) Deploy an agent - for now, we assume image exists
    #    and agent_config would come from a parsed manifest.
    example_agent_id = "test_agent_001"
    example_agent_config = {
        "runtime": {
            "image": "hello-world", # A simple image that just prints and exits
            "entrypoint": [] # For hello-world, no specific entrypoint override needed
        }
    }
    # await runner.deploy_agent(AgentManifest(agent_id=example_agent_id, version="0.1", name="Test Agent", runtime=example_agent_config["runtime"]))


    # 2. Run a task
    task_info = await runner.run_agent_task(
        agent_id=example_agent_id,
        task_description="Say hello",
        agent_config=example_agent_config
    )
    print(f"Task Info: {task_info}")

    if task_info.get("status") == "success":
        container_id = task_info.get("container_id")
        if container_id:
            # Wait a bit for the container to produce logs (hello-world is quick)
            import time
            time.sleep(2)

            # 3. Get logs
            logs = await runner.get_agent_logs(container_id, tail=10)
            print(f"\nLogs for {container_id}:\n{logs}")

            # 4. Stop task (hello-world usually exits on its own, but good to test stop)
            # await runner.stop_agent_task(container_id)
            # print(f"Task {container_id} stopped.")
    
    # 5. List running agents
    # running = await runner.list_running_agents()
    # print(f"\nCurrently running TetherCore agent containers (conceptual): {running}")


if __name__ == "__main__":
    # import asyncio
    # asyncio.run(_agent_runner_example()) # Commented out
    pass
