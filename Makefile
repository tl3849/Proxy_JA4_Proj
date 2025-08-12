# Proxy JA4 Project Makefile
# Provides convenient commands for managing the proxy testing environment

.PHONY: help up down build clean capture-start capture-stop parse test-all configs

# Default target
help:
	@echo "Proxy JA4 Project - Available Commands:"
	@echo ""
	@echo "Environment Management:"
	@echo "  make up          - Start all containers"
	@echo "  make down        - Stop and remove all containers"
	@echo "  make build       - Build all containers"
	@echo "  make clean       - Clean up containers, volumes, and images"
	@echo "  make rebuild     - Rebuild all containers from scratch"
	@echo ""
	@echo "Testing:"
	@echo "  make test-all    - Run full test suite for all proxy versions"
	@echo "  make test-squid  - Test Squid proxy specifically"
	@echo "  make test-mitm   - Test mitmproxy specifically"
	@echo ""
	@echo "Capture and Analysis:"
	@echo "  make capture-start - Start packet capture"
	@echo "  make capture-stop  - Stop packet capture"
	@echo "  make parse         - Parse JA4 signatures from captured traffic"
	@echo ""
	@echo "Configuration:"
	@echo "  make configs     - List available proxy configurations"
	@echo "  make cas         - Generate CA certificates"
	@echo ""
	@echo "Maintenance:"
	@echo "  make logs        - View container logs"
	@echo "  make status      - Check container status"
	@echo "  make shell       - Open shell in client container"

# Environment management
up:
	@echo "Starting all containers..."
	docker compose up -d
	@echo "Waiting for services to be ready..."
	@sleep 10
	@echo "Services started. Use 'make status' to check status."

down:
	@echo "Stopping all containers..."
	docker compose down
	@echo "All containers stopped."

build:
	@echo "Building all containers..."
	docker compose build
	@echo "Build completed."

rebuild:
	@echo "Rebuilding all containers from scratch..."
	docker compose build --no-cache
	@echo "Rebuild completed."

clean:
	@echo "Cleaning up containers, volumes, and images..."
	docker compose down -v --rmi all
	docker system prune -f
	@echo "Cleanup completed."

# Testing
test-all:
	@echo "Running full test suite for all proxy versions..."
	python scripts/proxy_manager.py --test-all

test-squid:
	@echo "Testing Squid proxy..."
	python scripts/proxy_manager.py --proxy squid --version 6.10

test-mitm:
	@echo "Testing mitmproxy..."
	python scripts/proxy_manager.py --proxy mitmproxy --version latest

# Capture and analysis
capture-start:
	@echo "Starting packet capture on Docker bridge interface..."
	@echo "Note: This will capture on the Docker bridge interface for proper traffic visibility"
	@echo "For Windows: Use 'make capture-start-windows' instead"
	@echo "For Linux/Mac: Use 'make capture-start-linux' instead"
	@echo "Or manually specify interface: python scripts/capture.py --start --interface br-<network-id> --output test.pcap"

capture-start-windows:
	@echo "Starting packet capture on Windows..."
	@echo "Please manually specify the Docker bridge interface:"
	@echo "1. Run: docker network inspect proxy_ja4_proj_pocnet --format='{{.Id}}'"
	@echo "2. Use the first 12 characters to form: br-<first-12-chars>"
	@echo "3. Run: python scripts/capture.py --start --interface br-<first-12-chars> --output test.pcap"

capture-start-linux:
	@echo "Starting packet capture on Linux/Mac..."
	python scripts/capture.py --start --interface "br-$$(docker network inspect proxy_ja4_proj_pocnet --format='{{.Id}}' | cut -c1-12)" --output test.pcap
	@echo "Packet capture started."

capture-stop:
	@echo "Stopping packet capture..."
	python scripts/capture.py --stop
	@echo "Packet capture stopped."

parse:
	@echo "Parsing JA4 signatures..."
	python scripts/parse_ja4.py
	@echo "JA4 analysis completed."

# Configuration management
configs:
	@echo "Available proxy configurations:"
	python scripts/config_manager.py --list

cas:
	@echo "Generating CA certificates..."
	python tests/install_proxy_cas.py
	@echo "CA certificates generated."

# Maintenance
logs:
	@echo "Container logs:"
	@echo "=== Squid ==="
	docker logs squid_poc 2>/dev/null || echo "Squid container not running"
	@echo ""
	@echo "=== mitmproxy ==="
	docker logs mitmproxy_poc 2>/dev/null || echo "mitmproxy container not running"
	@echo ""
	@echo "=== Client ==="
	docker logs client_poc 2>/dev/null || echo "Client container not running"

status:
	@echo "Container status:"
	docker compose ps

shell:
	@echo "Opening shell in client container..."
	docker exec -it client_poc /bin/bash

# Quick test sequence
quick-test: up
	@echo "Waiting for containers to be ready..."
	@sleep 30
	@echo "Starting packet capture..."
	@echo "Note: On Windows, you may need to manually specify the interface"
	@echo "Run: docker network inspect proxy_ja4_proj_pocnet --format='{{.Id}}'"
	@echo "Then use: python scripts/capture.py --start --interface br-<first-12-chars> --output test.pcap"
	@make capture-start
	@echo "Generating test traffic..."
	docker exec client_poc python test_all_proxies.py
	@echo "Stopping packet capture..."
	@make capture-stop
	@echo "Parsing JA4 signatures..."
	@make parse
	@echo "Quick test completed. Check captures/ja4_results.json for results."

# Windows-specific quick test
quick-test-windows: up
	@echo "Waiting for containers to be ready..."
	@sleep 30
	@echo "Starting packet capture..."
	@echo "Please manually start capture with:"
	@echo "python scripts/capture.py --start --interface br-<network-id> --output test.pcap"
	@echo "Generating test traffic..."
	docker exec client_poc python test_all_proxies.py
	@echo "Please manually stop capture with:"
	@echo "python scripts/capture.py --stop"
	@echo "Parsing JA4 signatures..."
	@make parse
	@echo "Quick test completed. Check captures/ja4_results.json for results."

# Development helpers
dev-setup: cas build
	@echo "Development environment setup completed."

dev-reset: down clean dev-setup
	@echo "Development environment reset completed."

# Proxy-specific operations
squid-only:
	@echo "Starting only Squid proxy..."
	docker compose up -d squid
	@echo "Squid started. Use 'make status' to check status."

mitm-only:
	@echo "Starting only mitmproxy..."
	docker compose up -d mitmproxy
	@echo "mitmproxy started. Use 'make status' to check status."

# Health checks
health:
	@echo "Checking container health..."
	@docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

# Backup and restore
backup:
	@echo "Creating backup of current configuration..."
	@mkdir -p backups
	@tar -czf backups/backup-$(shell date +%Y%m%d-%H%M%S).tar.gz \
		proxies/ captures/ logs/ docker-compose.yml
	@echo "Backup created in backups/ directory."

restore:
	@echo "Available backups:"
	@ls -la backups/ 2>/dev/null || echo "No backups found"
	@echo ""
	@echo "To restore, use: make restore-file FILE=backup-filename.tar.gz"

restore-file:
	@if [ -z "$(FILE)" ]; then \
		echo "Please specify backup file: make restore-file FILE=backup-filename.tar.gz"; \
		exit 1; \
	fi
	@echo "Restoring from $(FILE)..."
	@tar -xzf backups/$(FILE)
	@echo "Restore completed."

# Information
info:
	@echo "Proxy JA4 Project Information:"
	@echo "================================"
	@echo "Project Root: $(shell pwd)"
	@echo "Docker Compose Version: $(shell docker compose version --short)"
	@echo "Available Proxies:"
	@echo "  - Squid (SSL bumping)"
	@echo "  - mitmproxy (TLS inspection)"
	@echo "  - Bluecoat (placeholder)"
	@echo ""
	@echo "Use 'make help' for available commands"
	@echo "Use 'make configs' to see available configurations"
