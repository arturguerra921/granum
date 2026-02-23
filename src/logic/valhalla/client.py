import os
import requests
import json
import polyline

class ValhallaClient:
    def __init__(self, host=None):
        # Default to localhost if not set, or use environment variable
        self.host = host or os.environ.get('VALHALLA_HOST', 'http://localhost:8002')

    def get_matrix(self, origins, destinations, costing='auto'):
        """
        Calculates the distance matrix between origins and destinations.

        Args:
            origins (list of dict): List of {'lat': float, 'lon': float}
            destinations (list of dict): List of {'lat': float, 'lon': float}
            costing (str): Transportation mode (auto, bicycle, pedestrian, etc.)

        Returns:
            list of list: Matrix of distances (in km) where matrix[i][j] is the distance
                          from origin i to destination j. Returns None on error.
        """
        url = f"{self.host}/sources_to_targets"

        payload = {
            "sources": origins,
            "targets": destinations,
            "costing": costing,
            "units": "km"
        }

        try:
            response = requests.post(url, json=payload, timeout=600) # Long timeout for large matrices
            response.raise_for_status()
            data = response.json()

            # The response structure from sources_to_targets (matrix)
            # data['sources_to_targets'] is a list of lists
            if 'sources_to_targets' in data:
                return [[item['distance'] for item in row] for row in data['sources_to_targets']]

            return None

        except requests.exceptions.RequestException as e:
            print(f"Valhalla Matrix Error: {e}")
            return None
        except (KeyError, ValueError) as e:
            print(f"Valhalla Response Error: {e}")
            return None

    def get_route(self, origin, destination, costing='auto'):
        """
        Calculates the route between an origin and a destination.

        Args:
            origin (dict): {'lat': float, 'lon': float}
            destination (dict): {'lat': float, 'lon': float}
            costing (str): Transportation mode

        Returns:
            dict: Route data including geometry (decoded polyline) and summary.
                  Returns None on error.
        """
        url = f"{self.host}/route"

        payload = {
            "locations": [origin, destination],
            "costing": costing,
            "units": "km"
        }

        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()

            if 'trip' in data and 'legs' in data['trip']:
                # Decode the polyline for the entire trip
                # Valhalla returns shape in 1E6 precision
                geometry = []
                for leg in data['trip']['legs']:
                    if 'shape' in leg:
                         # Decode polyline (precision 6)
                         points = polyline.decode(leg['shape'], precision=6)
                         geometry.extend(points)

                return {
                    'geometry': geometry, # List of (lat, lon)
                    'distance': data['trip']['summary']['length'],
                    'time': data['trip']['summary']['time']
                }

            return None

        except requests.exceptions.RequestException as e:
            print(f"Valhalla Route Error: {e}")
            return None

if __name__ == "__main__":
    # Test
    client = ValhallaClient()
    # Mock data
    orgs = [{"lat": -15.7942, "lon": -47.8822}] # Brasilia
    dests = [{"lat": -16.6869, "lon": -49.2648}] # Goiania

    print("Testing Matrix...")
    # This will fail without the server running, but verifies imports
    try:
        print(client.get_matrix(orgs, dests))
    except:
        print("Server not reachable (Expected if not running)")
