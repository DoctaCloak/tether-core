# TetherCore: A Sovereign AI Companion

---

## Overview

TetherCore is a sovereign AI operating system designed to integrate into your life, built with memory, trust, privacy, and modular agency at its core. Unlike existing tools that commodify data and serve platforms, TetherCore exists solely to serve **you**. It aims to be a personal AI that learns you deeply over time, stores your personal data securely under your control, maps your memories, and optimizes your life through trusted, ethical interactions.

The relationship between the user and TetherCore is relational, not transactional. When you "Link" (connect), you grant the AI permission to walk with you. If trust is broken, you can "Shatter" the relationship, and the AI permanently deletes everything it knows about you, with provable deletion as a core tenet.

This project is currently in active development.

## Core Vision & Principles

- **Data Sovereignty:** You own your data. You can see it. You can delete it.
- **Total Transparency:** AI behavior, memory mapping, and suggestions are designed to be explainable.
- **Relational Intelligence:** TetherCore aims to learn your life like a trusted companion, not a mere servant.
- **Trust Before Power:** Features and interactions are gated behind user consent and trust milestones.
- **Privacy by Design:** Leveraging technologies like those from OpenMined (PySyft) for privacy-preserving computation and data handling.
- **Local-First Architecture:** Prioritizing local data storage and processing, with optional secure cloud fallback.
- **Modular Agency:** Utilizing "Mindscape Agents" – specialized AI modules for different aspects of your life, each with defined permissions.

## Key Features (Planned & In Development)

- 🧠 **Relational Memory Graph:** An encrypted and auditable system for storing "Echos" (memories, thoughts, goals) and mapping their connections.
- 🔗 **TetherChain:** A version control system for memory, logging changes, AI decisions, and enabling rollback for transparency and user control.
- 🛡️ **Privacy Enforcement:** Integration with PySyft for privacy-preserving machine learning and secure data handling.
- 🤖 **Mindscape Agents:** Modular, task-specific AI agents (e.g., CalendarMind, FocusMind) that operate within sandboxed environments and user-defined permissions.
- 🗣️ **Flexible AI Thinking Layer:** Using LiteLLM to route requests to various LLMs (local like Ollama/llama.cpp, or cloud-based) based on need and user preference.
- 📜 **Trust Contract & Consent Engine:** Explicit user agreements, clear data usage policies, and granular consent management for all AI actions.
- 💥 **Shatter Protocol:** A mechanism for provable and permanent deletion of all user data and AI persona upon user request.
- 🎤 **Voice Interface:** Planned integration with Whisper.cpp (speech-to-text) and Piper/Coqui (text-to-speech).
- 🖥️ **Trust Dashboard:** A user interface (React/D3.js) for visualizing memory maps, managing agents, permissions, and consent.
- CLI: A command-line interface for interacting with TetherCore's backend services.

## Technical Stack (High-Level)

- **Backend & AI Core:** Python
  - **LLM Routing:** LiteLLM
  - **Local LLMs:** Ollama, llama.cpp
  - **Privacy:** OpenMined (PySyft)
  - **Vector Storage:** Weaviate / Chroma
  - **Agent Runtime:** Docker, WebAssembly (exploration)
- **Command Line Interface (`tether-cli`):** Python (Click/Typer)
- **Frontend UI (`tether_dashboard`):** React, D3.js
- **Configuration:** YAML, `.env`
- **Testing:** Pytest, Ruff (linting)
- **CI/CD:** GitHub Actions

## Project Status

**Alpha / In Active Development.**

This project is currently being built by Christopher Taylor. The focus is on establishing the core infrastructure, memory system, and initial agent framework.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

- Python (version 3.10+ recommended)
- Poetry (for Python dependency management - recommended) or pip
- Git
- Docker (for running local services like Ollama, Weaviate/Chroma, and agent sandboxing)
- Node.js and npm/yarn (for the React UI, if you plan to run it)
- Access to local LLM instances (e.g., Ollama with models like Mistral, Llama 3, or Phi-3 downloaded)

### Installation

1.  **Clone the repository:**

    ```bash
    git clone [https://github.com/DoctaCloak/tether-core.git](https://github.com/DoctaCloak/tether-core.git) # Replace with your actual repo URL if different
    cd tethercore
    ```

2.  **Set up Python Environment & Install Dependencies:**

    - **Using Poetry (Recommended):**
      ```bash
      poetry install
      ```
    - **Using pip and `requirements.txt` (if you generate one):**
      ```bash
      python -m venv .venv
      source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
      pip install -r requirements.txt
      ```

3.  **Configuration:**

    - Copy the example configuration file:
      ```bash
      cp config/tether_config.yaml.example config/tether_config.yaml
      ```
    - Copy the example environment file:
      ```bash
      cp .env.example .env
      ```
    - Review `config/tether_config.yaml` and `.env` and update them with your local paths, API keys (if any for future cloud LLMs), and preferences.

4.  **Set up Local Services (Ollama, Vector DB):**
    - Ensure Ollama is running with your desired models.
    - Use the provided `docker-compose.yml` to start local services like Weaviate or Chroma (if configured):
      ```bash
      docker-compose up -d
      ```
    - _(Further instructions for setting up specific models with Ollama or configuring the vector DB will be added to `docs/development/setup_guide.md`)_

### Running TetherCore CLI

Once dependencies are installed and configurations are set:

- **Using Poetry:**
  ```bash
  poetry run tether-cli --help
  poetry run tether-cli echo create "My first TetherCore Echo!"
  ```
- **If using a virtual environment with pip:**
  ```bash
  source .venv/bin/activate # Or your venv activation command
  tether-cli --help
  tether-cli echo create "My first TetherCore Echo!"
  ```

### Running the UI (Tether Dashboard)

_(Instructions to be added once the UI development progresses. Typically involves `cd ui/tether_dashboard && npm install && npm start`)_

## Project Structure Overview

The project is organized into several key directories:

- `tethercore_cli/`: Source code for the command-line interface.
- `src/tethercore_engine/`: Core backend services and AI logic.
- `ui/tether_dashboard/`: React frontend application.
- `config/`: Application configuration files.
- `docs/`: Project documentation, including architecture and feasibility studies.
- `tests/`: Automated tests.
- `scripts/`: Utility scripts.

(Refer to `docs/architecture/system_overview.md` for a more detailed breakdown if available).

## Feasibility Studies & Hallucination Tracking

A core part of this project is understanding the capabilities and limitations, including potential "hallucinations" or unexpected behaviors of the AI components. Feasibility studies for each feature, along with tracking of observed issues, will be maintained in the `docs/feasibility_studies/` directory and linked to issues in the project tracker.

## Contributing

This is currently a solo project by [Your Name/GitHub Username]. However, guidelines for contributions (e.g., code style, pull request process) will be added here if the project opens up to collaboration in the future.

For now, feel free to:

- Open an issue for bugs or feature suggestions.
- Fork the repository and experiment.
