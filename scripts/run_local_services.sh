#!/bin/bash
# scripts/run_local_services.sh

# This script manages local development services for TetherCore using Docker Compose.
# It assumes you have a docker-compose.yml file in the project root.

# Exit immediately if a command exits with a non-zero status.
set -e

DOCKER_COMPOSE_FILE="docker-compose.yml"

# --- Helper Functions ---
check_docker_compose_file() {
    if [ ! -f "$DOCKER_COMPOSE_FILE" ]; then
        echo "❌ Error: Docker Compose file '$DOCKER_COMPOSE_FILE' not found in the project root."
        echo "   Please create one to define your local services (e.g., Ollama, Weaviate/Chroma)."
        exit 1
    fi
}

check_docker_running() {
    if ! docker info &> /dev/null; then
        echo "❌ Error: Docker daemon is not running. Please start Docker."
        exit 1
    fi
}

# --- Script Actions ---
action="$1"

if [ -z "$action" ]; then
    echo "Usage: $0 {start|stop|restart|status|logs|pull}"
    echo "Commands:"
    echo "  start   - Start all services defined in $DOCKER_COMPOSE_FILE in detached mode."
    echo "  stop    - Stop all services."
    echo "  restart - Restart all services."
    echo "  status  - Show the status of services."
    echo "  logs    - Tail logs from all services. Use 'logs <service_name>' for a specific service."
    echo "  pull    - Pull the latest images for services."
    echo "  down    - Stop and remove containers, networks, volumes, and images created by 'up'."
    exit 1
fi

# --- Pre-checks ---
check_docker_running
check_docker_compose_file

# --- Execute Action ---
case "$action" in
    start)
        echo "🚀 Starting local services via Docker Compose..."
        docker-compose -f "$DOCKER_COMPOSE_FILE" up --detach --remove-orphans
        echo "✅ Services started in detached mode."
        echo "   Use './scripts/run_local_services.sh status' to check their status."
        echo "   Use './scripts/run_local_services.sh logs' to view logs."
        ;;
    stop)
        echo "🛑 Stopping local services..."
        docker-compose -f "$DOCKER_COMPOSE_FILE" stop
        echo "✅ Services stopped."
        ;;
    restart)
        echo "🔄 Restarting local services..."
        docker-compose -f "$DOCKER_COMPOSE_FILE" stop
        docker-compose -f "$DOCKER_COMPOSE_FILE" up --detach --remove-orphans
        echo "✅ Services restarted."
        ;;
    status)
        echo "📊 Status of local services:"
        docker-compose -f "$DOCKER_COMPOSE_FILE" ps
        ;;
    logs)
        SERVICE_NAME="$2"
        if [ -n "$SERVICE_NAME" ]; then
            echo "📜 Tailing logs for service '$SERVICE_NAME' (Ctrl+C to stop)..."
            docker-compose -f "$DOCKER_COMPOSE_FILE" logs --follow --tail="50" "$SERVICE_NAME"
        else
            echo "📜 Tailing logs for all services (Ctrl+C to stop)..."
            docker-compose -f "$DOCKER_COMPOSE_FILE" logs --follow --tail="50"
        fi
        ;;
    pull)
        echo "⬇️ Pulling latest images for services..."
        docker-compose -f "$DOCKER_COMPOSE_FILE" pull
        echo "✅ Images pulled."
        ;;
    down)
        echo "🗑️ Stopping and removing containers, networks, and volumes..."
        echo "⚠️ This will remove data stored in volumes unless they are external."
        read -p "Are you sure you want to proceed? (y/N): " confirmation
        if [[ "$confirmation" =~ ^[Yy]$ ]]; then
            docker-compose -f "$DOCKER_COMPOSE_FILE" down --volumes # Use --volumes with caution
            echo "✅ Services and associated resources removed."
        else
            echo "ℹ️ Operation cancelled."
        fi
        ;;
    *)
        echo "❌ Error: Invalid action '$action'."
        echo "Usage: $0 {start|stop|restart|status|logs|pull|down}"
        exit 1
        ;;
esac

exit 0
