import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import timedelta

from mcp import ClientSession, StdioServerParameters
from requestcompletion.rc_mcp.main import MCPHttpParams
from requestcompletion import Node

# ================= START patch fixtures ================

@pytest.fixture
def patch_stdio_client():
    cm_mock = AsyncMock()
    cm_mock.__aenter__.return_value = (AsyncMock(), AsyncMock())
    cm_mock.__aexit__.return_value = None
    with patch("requestcompletion.rc_mcp.main.stdio_client", return_value=cm_mock) as p:
        yield p

@pytest.fixture
def mock_client_session():
    mock = MagicMock(spec=ClientSession)
    mock.initialize = AsyncMock()
    mock.list_tools = AsyncMock(return_value=MagicMock(tools=[{"name": "toolA"}]))
    mock.call_tool = AsyncMock(return_value=MagicMock(content="output"))
    return mock

@pytest.fixture
def patch_ClientSession(mock_client_session):
    cm_mock = AsyncMock()
    cm_mock.__aenter__.return_value = mock_client_session
    cm_mock.__aexit__.return_value = None
    with patch("requestcompletion.rc_mcp.main.ClientSession", return_value=cm_mock) as p:
        yield p

@pytest.fixture
def patch_streamablehttp_client():
    cm_mock = AsyncMock()
    cm_mock.__aenter__.return_value = (AsyncMock(), AsyncMock())
    cm_mock.__aexit__.return_value = None
    with patch("requestcompletion.rc_mcp.main.streamablehttp_client", return_value=cm_mock) as p:
        yield p

@pytest.fixture
def patch_sse_client():
    cm_mock = AsyncMock()
    cm_mock.__aenter__.return_value = (AsyncMock(), AsyncMock())
    cm_mock.__aexit__.return_value = None
    with patch("requestcompletion.rc_mcp.main.sse_client", return_value=cm_mock) as p:
        yield p

@pytest.fixture
def patch_httpx_AsyncClient():
    with patch("requestcompletion.rc_mcp.main.httpx.AsyncClient") as p:
        yield p

@pytest.fixture
def patch_CallbackServer():
    with patch("requestcompletion.rc_mcp.main.CallbackServer") as p:
        yield p

@pytest.fixture
def patch_OAuthClientProvider():
    with patch("requestcompletion.rc_mcp.main.OAuthClientProvider") as p:
        yield p

# ================= END patch fixtures =================

# ============ START value/object fixtures =============

@pytest.fixture
def mcp_http_params():
    return MCPHttpParams(
        url="http://test-url",
        headers={"Authorization": "Bearer fake"},
        timeout=timedelta(seconds=23),
        sse_read_timeout=timedelta(seconds=32),
        terminate_on_close=False
    )

@pytest.fixture
def stdio_config():
    return StdioServerParameters(command="dummy", args=[])

@pytest.fixture
def fake_tool():
    obj = MagicMock()
    obj.name = "abc"
    obj.to_dict = MagicMock(return_value={"name": "abc"})
    return obj

class DummyNode(Node):
    @classmethod
    def pretty_name(cls):
        return "DummyNode"

@pytest.fixture
def dummy_node():
    return DummyNode()

# ============ END value/object fixtures ===============