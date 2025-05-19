import yaml
import os
from pydantic import BaseModel, Field, HttpUrl, FilePath, DirectoryPath
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List, Dict, Any

# Define Pydantic models for different sections of your configuration
# to get type checking and validation.

class LLMRouterConfig(BaseModel):
    default_model: Optional[str] = "ollama/mistral" # Example default
    available_models: List[str] = Field(default_factory=lambda: ["ollama/mistral", "ollama/phi-3"])
    # Add API keys if LiteLLM doesn't manage them through its own env vars or proxy
    # openai_api_key: Optional[str] = Field(None, alias="OPENAI_API_KEY")
    # anthropic_api_key: Optional[str] = Field(None, alias="ANTHROPIC_API_KEY")
    verbose_litellm: bool = False

class VectorStoreConfig(BaseModel):
    provider: str = "weaviate" # "weaviate" or "chroma"
    weaviate_url: Optional[HttpUrl] = "http://localhost:8080"
    weaviate_api_key: Optional[str] = None
    chroma_path: Optional[DirectoryPath] = "./chroma_data" # Path for on-disk Chroma
    chroma_collection_name: str = "tether_echos"

class SyftConfig(BaseModel):
    use_local_virtual_worker: bool = True
    syft_node_url: Optional[HttpUrl] = None
    # Add syft credentials if needed for a remote node

class TetherChainConfig(BaseModel):
    log_file_path: FilePath = "tether_chain.log.jsonl" # Default path

class AgentRuntimeConfig(BaseModel):
    docker_socket_url: Optional[str] = None # e.g., "unix://var/run/docker.sock"

class VoiceInterfaceConfig(BaseModel):
    whisper_cpp_executable: Optional[str] = "main" # Assumes in PATH or provide full path
    whisper_model_path: Optional[FilePath] = "models/ggml-base.en.bin"
    piper_tts_executable: Optional[str] = "piper"
    piper_tts_model_path: Optional[FilePath] = None # e.g., "models/en_US-lessac-medium.onnx"
    piper_tts_config_path: Optional[FilePath] = None # e.g., "models/en_US-lessac-medium.onnx.json"

class AppConfig(BaseSettings):
    """
    Main application configuration model, loaded from YAML and environment variables.
    Pydantic-settings will automatically try to load from .env file and environment variables.
    """
    # Define how Pydantic-settings should load configurations
    model_config = SettingsConfigDict(
        env_file='.env',                # Load from .env file
        env_file_encoding='utf-8',
        env_nested_delimiter='__',      # For nested env vars like TETHERCORE__LLM_ROUTER__DEFAULT_MODEL
        extra='ignore'                  # Ignore extra fields in .env or environment
    )

    app_name: str = "TetherCore"
    environment: str = "development" # "development", "production", "testing"
    debug_mode: bool = Field(default=True, alias="TETHER_DEBUG_MODE")

    llm_router: LLMRouterConfig = Field(default_factory=LLMRouterConfig)
    vector_store: VectorStoreConfig = Field(default_factory=VectorStoreConfig)
    privacy_layer_syft: SyftConfig = Field(default_factory=SyftConfig)
    tether_chain: TetherChainConfig = Field(default_factory=TetherChainConfig)
    agent_runtime: AgentRuntimeConfig = Field(default_factory=AgentRuntimeConfig)
    voice_interface: VoiceInterfaceConfig = Field(default_factory=VoiceInterfaceConfig)

    # Example of a root-level env var that Pydantic-settings would pick up
    # TETHER_ADMIN_EMAIL: Optional[str] = None


_cached_config: Optional[AppConfig] = None

def load_app_config(config_file_path: str = "config/tether_config.yaml", force_reload: bool = False) -> AppConfig:
    """
    Loads application configuration from a YAML file, environment variables, and .env file.
    Uses Pydantic-settings for robust parsing and validation.
    Caches the loaded configuration to avoid repeated file I/O.

    Args:
        config_file_path (str): Path to the main YAML configuration file.
        force_reload (bool): If True, reloads the configuration even if cached.

    Returns:
        AppConfig: The loaded and validated application configuration.

    Raises:
        FileNotFoundError: If the YAML config file is not found.
        yaml.YAMLError: If there's an error parsing the YAML file.
        pydantic.ValidationError: If configuration values fail validation.
    """
    global _cached_config
    if _cached_config is not None and not force_reload:
        return _cached_config

    yaml_config = {}
    if os.path.exists(config_file_path):
        try:
            with open(config_file_path, 'r') as f:
                yaml_config = yaml.safe_load(f)
                if yaml_config is None: # Handle empty YAML file
                    yaml_config = {}
            print(f"Successfully loaded YAML config from: {config_file_path}")
        except FileNotFoundError:
            print(f"Warning: YAML config file not found at {config_file_path}. Using defaults and env vars.")
        except yaml.YAMLError as e:
            print(f"Error parsing YAML config file {config_file_path}: {e}")
            raise # Or handle more gracefully, e.g., by falling back to pure env/default
    else:
        print(f"Warning: YAML config file not found at {config_file_path}. Using defaults and env vars.")

    # Pydantic-settings will load from .env and environment variables automatically.
    # We pass the yaml_config as initial values. Values from .env/environment
    # will override values from the YAML file if they have the same path.
    try:
        # Pydantic-settings merges dicts deeply by default when models are nested.
        # So, yaml_config will provide base values, then .env, then actual environment variables.
        app_conf = AppConfig(**yaml_config)
        _cached_config = app_conf
        print("Application configuration loaded and validated successfully.")
        if app_conf.debug_mode:
            print("DEBUG MODE IS ENABLED.")
        return app_conf
    except Exception as e: # Catch Pydantic ValidationError specifically if needed
        print(f"Error validating application configuration: {e}")
        raise

# Example Usage:
if __name__ == "__main__":
    # Create a dummy config/tether_config.yaml for testing
    os.makedirs("config", exist_ok=True)
    dummy_yaml_content = """
app_name: "TetherCore (from YAML)"
environment: "test_yaml"
debug_mode: false # Overridden by env var if TETHER_DEBUG_MODE is set

llm_router:
  default_model: "ollama/phi-3-from-yaml"
  available_models:
    - "ollama/phi-3-from-yaml"
    - "ollama/mistral-from-yaml"

vector_store:
  provider: "chroma"
  chroma_path: "./test_chroma_data_yaml"
"""
    yaml_path = "config/tether_config.yaml"
    with open(yaml_path, 'w') as f:
        f.write(dummy_yaml_content)

    # Create a dummy .env file for testing
    dummy_env_content = """
TETHER_DEBUG_MODE=True
TETHERCORE__LLM_ROUTER__DEFAULT_MODEL="ollama/mistral-from-env"
TETHERCORE__VECTOR_STORE__WEAVIATE_URL="http://localhost:9090"
# TETHER_ADMIN_EMAIL="admin_from_env@example.com"
"""
    env_path = ".env"
    with open(env_path, 'w') as f:
        f.write(dummy_env_content)

    try:
        config = load_app_config(config_file_path=yaml_path)
        print("\n--- Loaded Config ---")
        print(config.model_dump_json(indent=2))

        print(f"\nApp Name: {config.app_name}") # Should be from YAML
        print(f"Environment: {config.environment}") # Should be from YAML
        print(f"Debug Mode: {config.debug_mode}") # Should be True (from .env)
        print(f"LLM Default Model: {config.llm_router.default_model}") # Should be from .env
        print(f"LLM Available Models: {config.llm_router.available_models}") # Should be from YAML
        print(f"Vector Store Provider: {config.vector_store.provider}") # Should be from YAML
        print(f"Chroma Path: {config.vector_store.chroma_path}") # Should be from YAML
        print(f"Weaviate URL: {config.vector_store.weaviate_url}") # Should be from .env
        # print(f"Admin Email: {config.TETHER_ADMIN_EMAIL}") # Should be from .env

    except Exception as e:
        print(f"Error in example: {e}")
    finally:
        # Clean up dummy files
        if os.path.exists(yaml_path): os.remove(yaml_path)
        if os.path.exists(env_path): os.remove(env_path)
        if os.path.exists("config") and not os.listdir("config"): os.rmdir("config")

