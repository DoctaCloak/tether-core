class TetherCoreException(Exception):
    """Base exception class for all TetherCore specific errors."""
    def __init__(self, message="An unspecified error occurred in TetherCore."):
        self.message = message
        super().__init__(self.message)

class ConfigException(TetherCoreException):
    """Exception raised for errors in configuration loading or validation."""
    def __init__(self, message="Configuration error."):
        super().__init__(message)

class InitializationError(TetherCoreException):
    """Exception raised when a service or component fails to initialize."""
    def __init__(self, component_name: str, message="Failed to initialize component."):
        self.component_name = component_name
        super().__init__(f"Initialization error in {component_name}: {message}")

class MemoryGraphException(TetherCoreException):
    """Exception related to Memory Graph operations."""
    def __init__(self, message="Memory Graph operation failed."):
        super().__init__(message)

class VectorStoreException(MemoryGraphException):
    """Specific exception for underlying vector store errors."""
    def __init__(self, message="Vector store operation failed."):
        super().__init__(message)

class LLMRouterException(TetherCoreException):
    """Exception related to LLM routing or LLM API errors."""
    def __init__(self, message="LLM Router operation failed."):
        super().__init__(message)

class PrivacyLayerException(TetherCoreException):
    """Exception related to privacy layer (e.g., PySyft) operations."""
    def __init__(self, message="Privacy layer operation failed."):
        super().__init__(message)

class TetherChainException(TetherCoreException):
    """Exception related to TetherChain operations."""
    def __init__(self, message="TetherChain operation failed."):
        super().__init__(message)

class AgentRuntimeException(TetherCoreException):
    """Exception related to the execution or management of Mindscape Agents."""
    def __init__(self, agent_id: str = "UnknownAgent", message="Agent runtime error."):
        self.agent_id = agent_id
        super().__init__(f"Error with agent '{agent_id}': {message}")

class AgentManifestException(AgentRuntimeException):
    """Exception for errors in parsing or validating agent manifests."""
    def __init__(self, message="Invalid agent manifest."):
        super().__init__(message=message) # agent_id might not be known yet

class ConsentException(TetherCoreException):
    """Exception related to consent management."""
    def __init__(self, message="Consent operation failed."):
        super().__init__(message)

class VoiceInterfaceException(TetherCoreException):
    """Exception related to STT/TTS operations."""
    def __init__(self, message="Voice interface operation failed."):
        super().__init__(message)

# Example usage:
if __name__ == "__main__":
    try:
        raise AgentRuntimeException(agent_id="focus_mind_v1", message="Container failed to start.")
    except TetherCoreException as e:
        print(f"Caught TetherCore Exception: {e}")
        if isinstance(e, AgentRuntimeException):
            print(f"Specifically, an Agent Runtime Exception for agent: {e.agent_id}")

    try:
        raise ConfigException("API key for LLM not found in configuration.")
    except ConfigException as e:
        print(f"Caught Config Exception: {e}")
