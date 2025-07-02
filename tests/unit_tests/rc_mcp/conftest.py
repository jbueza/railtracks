import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import timedelta

from mcp import ClientSession, StdioServerParameters
from requestcompletion.rc_mcp.main import MCPHttpParams, MCPAsyncClient
from requestcompletion import Node

import pytest
from unittest.mock import patch, AsyncMock

# ================= START patch fixtures ================
@pytest.fixture
def patch_stdio_client():
    cm_mock = AsyncMock()                   # This will act as the async context manager
    cm_mock.__aenter__.return_value = (AsyncMock(), AsyncMock())  # whatever stdio_client should return on enter
    cm_mock.__aexit__.return_value = None   # required for contextmanager protocol
    with patch("requestcompletion.rc_mcp.main.stdio_client", return_value=cm_mock) as p:
        yield p

@pytest.fixture
def patch_ClientSession(mock_client_session):
    cm_mock = AsyncMock()
    cm_mock.__aenter__.return_value = mock_client_session 
    cm_mock.__aexit__.return_value = None   # required for contextmanager protocol
    with patch("requestcompletion.rc_mcp.main.ClientSession", return_value=cm_mock) as p:
        yield p

@pytest.fixture
def patch_streamablehttp_client():
    with patch("requestcompletion.rc_mcp.main.streamablehttp_client", new_callable=AsyncMock) as p:
        yield p

@pytest.fixture
def patch_sse_client():
    with patch("requestcompletion.rc_mcp.main.sse_client", new_callable=AsyncMock) as p:
        yield p

@pytest.fixture
def patch_httpx_AsyncClient():
    with patch("requestcompletion.rc_mcp.main.httpx.AsyncClient") as _patch:
        yield _patch

@pytest.fixture
def patch_CallbackServer():
    with patch("requestcompletion.rc_mcp.main.CallbackServer") as p:
        yield p

@pytest.fixture
def patch_OAuthClientProvider():
    with patch("requestcompletion.rc_mcp.main.OAuthClientProvider") as p:
        yield p

# ================= END patch fixtures =================

# ============ START MCPHttpParams fixtures ============
@pytest.fixture
def mcp_http_params():
    return MCPHttpParams(
        url="http://test-url",
        headers={"Authorization": "Bearer fake"},
        timeout=timedelta(seconds=23),
        sse_read_timeout=timedelta(seconds=32),
        terminate_on_close=False
    )

# ============ END MCPHttpParams fixtures ==============

# ============ START stdio config fixture ==============
@pytest.fixture
def stdio_config():
    return StdioServerParameters(command="dummy", args=[])
# ============ END stdio config fixture ===============

# ============ START mock client session ==============
@pytest.fixture
def mock_client_session():
    mock = MagicMock(spec=ClientSession)
    mock.initialize = AsyncMock()
    mock.list_tools = AsyncMock(return_value=MagicMock(tools=[{"name": "toolA"}]))
    mock.call_tool = AsyncMock(return_value=MagicMock(content="output"))
    return mock
# ============ END mock client session ================

# =========== START mock tool object ==================
@pytest.fixture
def fake_tool():
    obj = MagicMock()
    obj.name = "abc"
    obj.to_dict = MagicMock(return_value={"name": "abc"})
    return obj
# =========== END mock tool object ====================

# ========= START mock Node for from_mcp ==============
class DummyNode(Node):
    @classmethod
    def pretty_name(cls):
        return "DummyNode"
    

@pytest.fixture
def dummy_node():
    return DummyNode()
# ========= END mock Node for from_mcp ================