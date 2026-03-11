import sys
sys.path.append('.')
from src.view.view import app

if __name__ == "__main__":
    app.run(debug=True, port=8050)
