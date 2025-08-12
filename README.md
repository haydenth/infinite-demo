# Cross-Border Payment API

A REST API system demonstrating USD → multi-currency payout flow with a fee engine, built using microservices architecture.

## Architecture

This system consists of three main services:

- **Onramp Service** (Port 8080): Handles USD collection and USDC conversion
- **Offramp Service** (Port 20001): Manages USDC to local currency conversion and payouts  
- **PostgreSQL Database** (Port 5432): Persistent data storage

## Services Overview

### Onramp Service
- Accepts USD payments via various methods (credit card, bank transfer, ACH)
- Converts USD to USDC using mock exchange rates
- Provides payment validation and failure simulation
- Web interface available at root endpoint

### Offramp Service  
- Converts USDC to local currencies
- Handles bank payouts and transfers
- Provides exchange rate information
- Supports multiple destination currencies

### Database
- PostgreSQL 16 for persistent data storage
- Shared between services via Docker network
- Data persisted in named volume

## Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Ports 8080, 20001, and 5432 available

### Starting the Services

1. **Clone and navigate to the project:**
   ```bash
   cd /path/to/infinite.dev
   ```

2. **Start all services:**
   ```bash
   docker-compose up -d
   ```

3. **View logs (optional):**
   ```bash
   docker-compose logs -f
   ```

### Service URLs

Once running, the services are available at:

- **Onramp Service**: http://localhost:8080
- **Offramp Service**: http://localhost:20001  
- **PostgreSQL**: localhost:5432

### Health Checks

Verify services are running:
```bash
# Onramp service
curl http://localhost:8080/health

# Offramp service  
curl http://localhost:20001/health
```

## Development

### Service Details

For detailed API documentation:
- **Onramp Service**: See `onramp-service/README.md`
- **Offramp Service**: See `offramp-service/README.md`

### Environment Variables

Service configuration is managed through the `env_vars` file.

### Stopping Services

```bash
docker-compose down
```

To remove volumes (deletes database data):
```bash
docker-compose down -v
```

## Project Structure

```
.
├── README.md                 # This file - project overview and setup
├── FINANCE.md               # Challenge requirements and evaluation criteria
├── docker-compose.yml       # Service orchestration
├── env_vars                 # Environment configuration
├── onramp-service/          # USD collection and USDC conversion
│   ├── app.py
│   ├── Dockerfile
│   └── README.md
└── offramp-service/         # USDC to local currency conversion
    ├── app.py
    ├── Dockerfile
    └── README.md
```

## Additional Information

For challenge requirements, evaluation criteria, and detailed specifications, see `FINANCE.md`.
