import os
import requests
import json
import logging

class ValhallaClient:
    def __init__(self, base_url="http://localhost:8002"):
        # Allow overriding via environment variable, default to localhost for testing outside docker
        # In docker, it will be http://valhalla:8002
        self.base_url = os.environ.get("VALHALLA_URL", base_url)
        self.logger = logging.getLogger(__name__)

    def _chunk_list(self, lst, n):
        """Yield successive n-sized chunks from lst."""
        for i in range(0, len(lst), n):
            yield lst[i:i + n]

    def get_matrix(self, sources, targets, costing="auto"):
        """
        Get distance matrix from sources to targets.
        sources: list of {'lat': float, 'lon': float}
        targets: list of {'lat': float, 'lon': float}

        Returns: List of lists (matrix).
                 matrix[source_index][target_index] = {'distance': float, 'time': int}
        """
        url = f"{self.base_url}/sources_to_targets"

        # Configurable chunk sizes
        source_chunk_size = 50
        target_chunk_size = 50

        full_matrix = []

        self.logger.info(f"Calculating matrix for {len(sources)} sources and {len(targets)} targets.")

        for source_chunk in self._chunk_list(sources, source_chunk_size):
            # Prepare rows for this source chunk
            row_results = [[] for _ in range(len(source_chunk))]

            for target_chunk in self._chunk_list(targets, target_chunk_size):
                payload = {
                    "sources": source_chunk,
                    "targets": target_chunk,
                    "costing": costing,
                    "units": "km"
                }

                try:
                    response = requests.post(url, json=payload)
                    response.raise_for_status()
                    data = response.json()

                    # data['sources_to_targets'] is a list of lists
                    matrix_chunk = data.get("sources_to_targets", [])

                    if not matrix_chunk:
                         # Should not happen on success, but handle empty response
                         for i in range(len(source_chunk)):
                             row_results[i].extend([None] * len(target_chunk))
                    else:
                        for i, row in enumerate(matrix_chunk):
                            # row is a list of results for source i against all targets in target_chunk
                            row_results[i].extend(row)

                except Exception as e:
                    self.logger.error(f"Error fetching matrix chunk: {e}")
                    # Fill with None or error dict
                    for i in range(len(source_chunk)):
                        row_results[i].extend([{'distance': None, 'time': None}] * len(target_chunk))

            full_matrix.extend(row_results)

        return full_matrix

    def get_route(self, origin, destination, costing="auto"):
        """
        Get route geometry from origin to destination.
        """
        url = f"{self.base_url}/route"

        payload = {
            "locations": [origin, destination],
            "costing": costing,
            "units": "km"
        }

        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"Error fetching route: {e}")
            return None
