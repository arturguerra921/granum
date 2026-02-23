# Granum Project

This project includes a routing optimization module using OSRM.

## Docker Workflow (Recommended)

This workflow sets up the application along with a local OSRM instance for routing calculations.

### Prerequisites

*   Docker and Docker Compose installed.
*   (Optional) Python 3.10+ for running the setup script (or just run the commands manually).

### 1. Setup OSRM Data

Run the setup script to download and process the OpenStreetMap data for Brazil. This step downloads ~400MB (filtered) to ~3GB (raw) of data and processes it, which may take some time (10-30 mins depending on your machine).

**Linux / Mac:**
```bash
python3 scripts/setup_osrm.py
```

**Windows:**
```powershell
python scripts/setup_osrm.py
```

*Note: This script requires Docker to be running, as it uses `osmium` and `osrm-backend` containers to process the data.*

### 2. Run the Application

Start the application and the OSRM service:

```bash
docker-compose up --build
```

The application will be available at `http://localhost:8050`.
The OSRM service will be available at `http://localhost:5000`.

## Legacy Development Workflow (Local Python)

### On Linux / Mac (Makefile)

1.  **First Time Setup:**
    ```bash
    make setup
    ```

2.  **Run Application:**
    ```bash
    make run
    ```
    This automatically checks if port 8050 is free and starts the server.

3.  **Clean Up:**
    ```bash
    make clean
    ```

### On Windows (PowerShell)

1.  **First Time Setup:**
    Open PowerShell in the root directory and run:
    ```powershell
    .\scripts\setup.ps1
    ```

2.  **Run Application:**
    To run the app (and kill any existing instance automatically):
    ```powershell
    .\scripts\run.ps1
    ```

Note: You may need to run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process` if scripts are disabled.

## OSRM Integration

To use the OSRM service in your code, import the client:

```python
from src.logic.osrm import OSRMClient

client = OSRMClient(base_url="http://osrm:5000") # Use localhost:5000 if running outside docker
# or http://osrm:5000 if running inside docker-compose

# Get distance matrix
# origins and destinations are lists of (lat, lon) tuples
dist_matrix = client.get_distance_matrix(origins, destinations)
```
