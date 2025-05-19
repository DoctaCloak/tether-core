from pydantic import BaseModel, Field, validator, HttpUrl
from typing import List, Optional, Dict, Any, Union
import yaml
import json

class AgentRuntimeConfig(BaseModel):
    """Configuration for the agent's runtime environment."""
    type: str = Field(..., description="Type of runtime, e.g., 'docker', 'wasm'.")
    image: Optional[str] = Field(None, description="Docker image name (if type is 'docker').")
    wasm_path: Optional[str] = Field(None, description="Path or URL to WASM module (if type is 'wasm').")
    entrypoint: Optional[List[str]] = Field(default_factory=list, description="Entrypoint command for the runtime.")
    env_vars: Optional[Dict[str, str]] = Field(default_factory=dict, description="Environment variables to set.")
    # Add other runtime-specific configs: resources (cpu, memory), network, volumes etc.

class AgentPermission(BaseModel):
    """Defines a permission required by the agent."""
    resource: str = Field(..., description="The resource the permission applies to (e.g., 'memory_graph', 'calendar', 'llm').")
    actions: List[str] = Field(..., description="List of actions allowed on the resource (e.g., 'read', 'write', 'query').")
    conditions: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Conditions for the permission (e.g., specific tags, time limits).")

class AgentLLMConfig(BaseModel):
    """Configuration for LLM usage by the agent."""
    preferred_models: Optional[List[str]] = Field(default_factory=list, description="List of preferred LLM models or model types.")
    max_tokens_per_request: Optional[int] = Field(None, description="Max tokens the agent can request from an LLM.")
    # Other LLM related constraints or preferences

class AgentManifest(BaseModel):
    """
    Represents the manifest file for a Mindscape Agent.
    Defines its identity, capabilities, runtime, and requirements.
    """
    agent_id: str = Field(..., description="Unique identifier for the agent (e.g., 'focus_mind_v1').")
    version: str = Field(..., description="Version of the agent.")
    name: str = Field(..., description="Human-readable name of the agent.")
    description: Optional[str] = Field(None, description="A brief description of what the agent does.")
    author: Optional[str] = Field(None, description="Author or maintainer of the agent.")
    
    runtime: AgentRuntimeConfig = Field(..., description="Configuration for the agent's execution environment.")
    permissions_requested: List[AgentPermission] = Field(default_factory=list, description="List of permissions the agent requests.")
    
    llm_config: Optional[AgentLLMConfig] = Field(None, description="Configuration related to LLM usage by the agent.")
    
    # input_schema: Optional[Dict[str, Any]] = Field(None, description="JSON Schema defining the expected input for the agent's tasks.")
    # output_schema: Optional[Dict[str, Any]] = Field(None, description="JSON Schema defining the expected output from the agent.")
    
    tags: Optional[List[str]] = Field(default_factory=list, description="Keywords or tags for categorizing the agent.")
    custom_config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Agent-specific custom configuration parameters.")

    @validator('agent_id')
    def agent_id_format(cls, value):
        # Example validator: agent_id should be simple, no spaces
        if not value.isalnum() and '_' not in value and '-' not in value:
            raise ValueError("agent_id must be alphanumeric with optional underscores/hyphens.")
        return value.lower()


def parse_agent_manifest(file_path: str) -> Optional[AgentManifest]:
    """
    Parses an agent manifest file (JSON or YAML) into an AgentManifest object.

    Args:
        file_path (str): The path to the manifest file.

    Returns:
        Optional[AgentManifest]: The parsed AgentManifest object, or None if parsing fails.
    """
    try:
        with open(file_path, 'r') as f:
            if file_path.endswith(".yaml") or file_path.endswith(".yml"):
                manifest_data = yaml.safe_load(f)
            elif file_path.endswith(".json"):
                manifest_data = json.load(f)
            else:
                print(f"Unsupported manifest file format: {file_path}. Please use JSON or YAML.")
                return None
        
        return AgentManifest(**manifest_data)
    except FileNotFoundError:
        print(f"Manifest file not found: {file_path}")
        return None
    except (yaml.YAMLError, json.JSONDecodeError) as e:
        print(f"Error parsing manifest file {file_path}: {e}")
        return None
    except Exception as pydantic_e: # Catch Pydantic validation errors
        print(f"Validation error in manifest file {file_path}: {pydantic_e}")
        return None

# Example Usage
if __name__ == "__main__":
    # Create a dummy YAML manifest file for testing
    dummy_manifest_yaml_content = """
agent_id: "example_focus_agent_v1"
version: "1.0.2"
name: "Example Focus Agent"
description: "A sample agent that helps with focus tasks."
author: "TetherCore Dev Team"
runtime:
  type: "docker"
  image: "tethercore/focus_agent:1.0.2"
  entrypoint: ["python", "agent_main.py"]
  env_vars:
    LOG_LEVEL: "INFO"
permissions_requested:
  - resource: "memory_graph"
    actions: ["read", "write_echo"]
    conditions:
      tags_allowed: ["focus", "work"]
  - resource: "llm"
    actions: ["query"]
llm_config:
  preferred_models: ["ollama/mistral", "ollama/phi-3"]
  max_tokens_per_request: 1000
tags: ["productivity", "focus", "example"]
custom_config:
  default_focus_duration_minutes: 25
"""
    dummy_yaml_path = "dummy_agent_manifest.yaml"
    with open(dummy_yaml_path, 'w') as f:
        f.write(dummy_manifest_yaml_content)

    parsed_manifest = parse_agent_manifest(dummy_yaml_path)
    if parsed_manifest:
        print("Successfully parsed agent manifest:")
        print(parsed_manifest.model_dump_json(indent=2))
        print(f"\nAgent Name: {parsed_manifest.name}")
        print(f"Runtime Image: {parsed_manifest.runtime.image}")
        if parsed_manifest.permissions_requested:
            print(f"First permission resource: {parsed_manifest.permissions_requested[0].resource}")
    else:
        print("Failed to parse agent manifest.")

    # Clean up dummy file
    import os
    os.remove(dummy_yaml_path)

    # Example of a manifest that would fail validation
    invalid_manifest_content = """
agent_id: "invalid agent id with spaces" # This will fail validation
version: "0.1"
name: "Invalid Agent"
runtime:
  type: "docker"
"""
    invalid_yaml_path = "invalid_manifest.yaml"
    with open(invalid_yaml_path, 'w') as f:
        f.write(invalid_manifest_content)
    
    print("\nAttempting to parse invalid manifest:")
    parse_agent_manifest(invalid_yaml_path)
    os.remove(invalid_yaml_path)
