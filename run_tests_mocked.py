import sys
import unittest
from unittest.mock import MagicMock

def mock_dependencies():
    class MockRequestException(Exception):
        pass

    sys.modules['pandas'] = MagicMock()
    sys.modules['numpy'] = MagicMock()

    # Needs to mock pyomo.environ specifically
    pyomo_mock = MagicMock()
    pyomo_environ_mock = MagicMock()
    pyomo_mock.environ = pyomo_environ_mock
    sys.modules['pyomo'] = pyomo_mock
    sys.modules['pyomo.environ'] = pyomo_environ_mock
    sys.modules['pyomo.opt'] = MagicMock()

    sys.modules['psutil'] = MagicMock()
    sys.modules['diskcache'] = MagicMock()

    requests_mock = MagicMock()
    requests_mock.RequestException = MockRequestException
    sys.modules['requests'] = requests_mock

    sys.modules['multiprocess'] = MagicMock()
    sys.modules['dash'] = MagicMock()
    sys.modules['dash_bootstrap_components'] = MagicMock()
    sys.modules['plotly'] = MagicMock()
    sys.modules['plotly.express'] = MagicMock()
    sys.modules['plotly.graph_objects'] = MagicMock()
    sys.modules['flask'] = MagicMock()
    sys.modules['werkzeug'] = MagicMock()
    sys.modules['werkzeug.utils'] = MagicMock()

mock_dependencies()

if __name__ == '__main__':
    # test_conab_parse does pandas stuff outside class, run discover but skip failing non-related tests
    # or just run it via pytest to isolate
    pass
