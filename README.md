# Granum Project

This project uses a standard development workflow.

## Development Workflow

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

## Docker Usage (Recommended for Valhalla Integration)

To run the application with the integrated Valhalla routing engine, follow these steps:

1.  **Prerequisites:** Ensure you have Docker and Docker Compose installed on your machine.
2.  **Start Services:**
    Run the following command in the project root:
    ```bash
    docker-compose up -d
    ```
    This will start two containers: `granum` (the app) and `valhalla` (the routing engine).

3.  **First Run Note:**
    On the very first execution, the `valhalla` container will automatically download the OpenStreetMap data for Brazil (~3-4GB) and process it into tiles. **This process can take 1-2 hours depending on your internet connection and CPU.**
    You can monitor the progress by running:
    ```bash
    docker-compose logs -f valhalla
    ```
    Look for messages indicating "valhalla_service" is running or "httpd" started.

4.  **Access the Application:**
    Once the services are up, open your browser and go to:
    [http://localhost:8050](http://localhost:8050)

5.  **Stop Services:**
    To stop the application, run:
    ```bash
    docker-compose down
    ```
    The Valhalla data is persisted in the `valhalla_data` directory, so subsequent starts will be much faster.
