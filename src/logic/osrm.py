import requests
import math
from typing import List, Tuple, Optional

class OSRMClient:
    def __init__(self, base_url: str = "http://osrm:5000", max_table_size: int = 100):
        self.base_url = base_url.rstrip("/")
        self.max_table_size = max_table_size

    def get_distance_matrix(self, origins: List[Tuple[float, float]], destinations: List[Tuple[float, float]]) -> List[List[Optional[float]]]:
        """
        Calculates the distance matrix between origins and destinations using OSRM Table API.

        Args:
            origins: List of (latitude, longitude) tuples.
            destinations: List of (latitude, longitude) tuples.

        Returns:
            A 2D list (matrix) where matrix[i][j] is the distance in meters from origins[i] to destinations[j].
            Returns None for unreachable pairs.
        """
        if not origins or not destinations:
            return []

        # Initialize result matrix with None
        num_origins = len(origins)
        num_destinations = len(destinations)
        matrix = [[None for _ in range(num_destinations)] for _ in range(num_origins)]

        # Chunk processing to respect OSRM limits
        # We need to split origins and destinations such that the total number of coordinates
        # sent in one request does not exceed max_table_size.
        # Actually, for table service, max_table_size is typically the total number of coordinates in the URL.
        # Let's say we split origins into chunks of size A and destinations into chunks of size B
        # such that A + B <= max_table_size.
        # A safe bet is max_table_size // 2 for both.

        chunk_size = self.max_table_size // 2

        for i in range(0, num_origins, chunk_size):
            origin_chunk = origins[i : i + chunk_size]
            origin_indices = range(len(origin_chunk))

            for j in range(0, num_destinations, chunk_size):
                dest_chunk = destinations[j : j + chunk_size]
                dest_indices = range(len(origin_chunk), len(origin_chunk) + len(dest_chunk))

                # Prepare coordinates list: origins first, then destinations
                # OSRM expects: lon,lat
                coords = [f"{lon},{lat}" for lat, lon in origin_chunk] + \
                         [f"{lon},{lat}" for lat, lon in dest_chunk]

                coords_str = ";".join(coords)

                # Construct query
                # sources=0;1;2... (indices of origins in coords list)
                # destinations=3;4;5... (indices of destinations in coords list)
                sources_str = ";".join(map(str, origin_indices))
                dest_str = ";".join(map(str, dest_indices))

                url = f"{self.base_url}/table/v1/driving/{coords_str}?sources={sources_str}&destinations={dest_str}&annotations=distance"

                try:
                    response = requests.get(url)
                    response.raise_for_status()
                    data = response.json()

                    if data["code"] != "Ok":
                        print(f"OSRM Error: {data.get('message', 'Unknown error')}")
                        continue

                    distances = data["distances"]

                    # Fill the result matrix
                    for r_idx, row in enumerate(distances):
                        for c_idx, dist in enumerate(row):
                            # matrix[i + r_idx][j + c_idx] = dist
                            # Handle None (unreachable)
                            if dist is not None:
                                matrix[i + r_idx][j + c_idx] = float(dist)
                            else:
                                matrix[i + r_idx][j + c_idx] = None

                except requests.RequestException as e:
                    print(f"Request failed: {e}")
                    # Keep None in matrix for failed chunks
                    pass

        return matrix

# Example usage (commented out)
# if __name__ == "__main__":
#     client = OSRMClient()
#     origins = [(-15.7942, -47.8822), (-16.6869, -49.2648)] # Brasilia, Goiania
#     destinations = [(-23.5505, -46.6333)] # Sao Paulo
#     dist_matrix = client.get_distance_matrix(origins, destinations)
#     print(dist_matrix)
