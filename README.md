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
