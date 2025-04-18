# Default target
help:
	@echo "Available commands:"
	@echo "  make up      - Start the domain health checker container"
	@echo "  make down    - Stop and remove the domain health checker container"

# Start the container
up:
	@echo "Starting Domain Health Checker..."
	docker compose up --build
	@echo "Container started. Use 'docker-compose logs -f' to view logs."

# Stop and remove the container
down:
	@echo "Stopping Domain Health Checker..."
	docker compose down
	@echo "Container stopped and removed."