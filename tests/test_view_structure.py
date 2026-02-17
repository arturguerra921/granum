import sys
import os

# Add src to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from src.view.view import app, view
except ImportError as e:
    print(f"Failed to import app: {e}")
    sys.exit(1)

def test_app_structure():
    print("Testing app structure...")
    if app.layout is None:
        print("App layout is None")
        sys.exit(1)

    # Check callback registration
    callbacks = app.callback_map
    print(f"Number of callbacks: {len(callbacks)}")

    if len(callbacks) == 0:
        print("No callbacks registered")
        sys.exit(1)

    # Simple check for specific input components in callbacks
    inputs_found = set()
    for cb in callbacks.values():
        for inp in cb['inputs']:
            inputs_found.add(inp['id'])

    print(f"Inputs found in callbacks: {inputs_found}")

    expected_inputs = {'main-tabs', 'upload-data'}
    if not expected_inputs.issubset(inputs_found):
        print(f"Missing expected inputs in callbacks. Expected {expected_inputs}, found {inputs_found}")
        sys.exit(1)

    print("Structure test passed!")

if __name__ == "__main__":
    test_app_structure()
