import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.view.view import app

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=8050)
