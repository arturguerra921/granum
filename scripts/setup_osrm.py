import os
import subprocess
import sys
import shutil

# Configuration
OSM_PBF_URL = "https://download.geofabrik.de/south-america/brazil-latest.osm.pbf"
DATA_DIR = os.path.join(os.getcwd(), "data", "osrm")
OSM_PBF_FILE = "brazil-latest.osm.pbf"
FILTERED_PBF_FILE = "brazil-filtered.osm.pbf"
OSRM_FILE_BASE = "brazil-filtered.osrm"

# Filter tags based on user requirements (added service and track for rural areas)
FILTER_TAGS = "w/highway=motorway,trunk,primary,secondary,tertiary,unclassified,residential,service,track"

def run_command(command, check=True):
    """Runs a shell command and prints output."""
    print(f"Running: {command}")
    try:
        subprocess.run(command, shell=True, check=check, text=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {command}")
        print(e)
        sys.exit(1)

def ensure_docker():
    """Checks if Docker is installed and running."""
    try:
        subprocess.run(["docker", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: Docker is not installed or not in PATH.")
        sys.exit(1)

def download_pbf():
    """Downloads the Brazil OSM PBF file if it doesn't exist."""
    pbf_path = os.path.join(DATA_DIR, OSM_PBF_FILE)
    if os.path.exists(pbf_path):
        print(f"File {pbf_path} already exists. Skipping download.")
        return

    print(f"Downloading {OSM_PBF_URL}...")
    import urllib.request

    # Create directory if not exists
    os.makedirs(DATA_DIR, exist_ok=True)

    def report(block_num, block_size, total_size):
        downloaded = block_num * block_size
        if total_size > 0:
            percent = downloaded * 100 / total_size
            sys.stdout.write(f"\rDownloading... {percent:.2f}% ({downloaded / (1024*1024):.1f} MB)")
            sys.stdout.flush()

    urllib.request.urlretrieve(OSM_PBF_URL, pbf_path, reporthook=report)
    print("\nDownload complete.")

def filter_pbf():
    """Filters the PBF file using osmium inside a Docker container."""
    input_path = os.path.join(DATA_DIR, OSM_PBF_FILE)
    output_path = os.path.join(DATA_DIR, FILTERED_PBF_FILE)

    if os.path.exists(output_path):
        print(f"Filtered file {output_path} already exists. Skipping filtering.")
        return

    print("Filtering PBF file with osmium...")
    # Use debian:bullseye-slim to install osmium-tool and run it
    # We mount the DATA_DIR to /data

    # Command to run inside the container
    # 1. Update apt
    # 2. Install osmium-tool
    # 3. Run osmium tags-filter

    docker_cmd = (
        f"docker run --rm -v \"{DATA_DIR}:/data\" debian:bullseye-slim "
        f"bash -c \"apt-get update && apt-get install -y osmium-tool && "
        f"osmium tags-filter /data/{OSM_PBF_FILE} {FILTER_TAGS} -o /data/{FILTERED_PBF_FILE}\""
    )
    run_command(docker_cmd)
    print("Filtering complete.")

def process_osrm():
    """Runs OSRM extraction and contraction."""
    # Check if .osrm.hsgr exists (result of contraction)
    hsgr_path = os.path.join(DATA_DIR, f"{OSRM_FILE_BASE}.hsgr")
    if os.path.exists(hsgr_path):
        print(f"OSRM data {hsgr_path} already exists. Skipping processing.")
        return

    print("Processing OSRM data (Extract & Contract)...")

    # Create .stxxl config for disk-based processing (avoid OOM)
    # This tells OSRM to use a 30GB swap file in /data/stxxl (20GB+ safe margin)
    stxxl_path = os.path.join(DATA_DIR, ".stxxl")
    with open(stxxl_path, "w") as f:
        f.write("disk=/data/stxxl,30000,syscall")

    # 1. Extract
    # We use -t 4 to limit threads (reduce memory usage per thread)
    # We mount the .stxxl file to /opt/.stxxl (where OSRM looks for it by default or we set env var)
    # Actually easier to just map it to /data/.stxxl and point STXXLCFG env var
    extract_cmd = (
        f"docker run --rm -v \"{DATA_DIR}:/data\" -e STXXLCFG=/data/.stxxl osrm/osrm-backend "
        f"osrm-extract -p /opt/car.lua /data/{FILTERED_PBF_FILE} -t 4"
    )
    print("Running extraction (this may take a while using disk swap)...")
    run_command(extract_cmd)

    # 2. Partition (MLD) - Partition the graph
    partition_cmd = (
        f"docker run --rm -v \"{DATA_DIR}:/data\" -e STXXLCFG=/data/.stxxl osrm/osrm-backend "
        f"osrm-partition /data/{OSRM_FILE_BASE} -t 4"
    )
    print("Running partitioning (MLD)...")
    run_command(partition_cmd)

    # 3. Customize (MLD) - Customize the graph
    customize_cmd = (
        f"docker run --rm -v \"{DATA_DIR}:/data\" -e STXXLCFG=/data/.stxxl osrm/osrm-backend "
        f"osrm-customize /data/{OSRM_FILE_BASE} -t 4"
    )
    print("Running customization (MLD)...")
    run_command(customize_cmd)

    # Cleanup stxxl file to free space
    stxxl_data = os.path.join(DATA_DIR, "stxxl")
    if os.path.exists(stxxl_data):
        try:
            os.remove(stxxl_data)
        except OSError:
            pass

    # Cleanup intermediate files? Maybe keep them for now.
    print("OSRM processing complete.")

def main():
    print("Starting OSRM Setup...")
    ensure_docker()

    # Ensure data directory exists
    os.makedirs(DATA_DIR, exist_ok=True)

    download_pbf()
    filter_pbf()
    process_osrm()

    print("\nSetup finished successfully!")
    print(f"Data is ready in {DATA_DIR}")
    print("You can now run 'docker-compose up' to start the application.")

if __name__ == "__main__":
    main()
