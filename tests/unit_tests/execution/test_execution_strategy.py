
import pytest
from unittest.mock import AsyncMock, patch

from src.requestcompletion.execution.execution_strategy import AsyncioExecutionStrategy
from src.requestcompletion.pubsub.messages import RequestSuccess, RequestFailure

# ============ START AsyncioExecutionStrategy Success Tests ===============
@pytest.mark.asyncio
@patch("src.requestcompletion.execution.execution_strategy.get_publisher")
@patch("src.requestcompletion.execution.execution_strategy.NodeState")
async def test_asyncio_execution_strategy_success(mock_node_state, mock_get_publisher, mock_task, mock_publisher):
    mock_get_publisher.return_value = mock_publisher
    mock_task.invoke = AsyncMock(return_value="ok")
    mock_node_state.return_value = "node-state"

    strat = AsyncioExecutionStrategy()
    response = await strat.execute(mock_task)

    assert isinstance(response, RequestSuccess)
    assert response.result == "ok"
    assert response.node_state == "node-state"
    mock_publisher.publish.assert_awaited_once_with(response)
# ============ END AsyncioExecutionStrategy Success Tests ===============

# ============ START AsyncioExecutionStrategy Failure Tests ===============
@pytest.mark.asyncio
@patch("src.requestcompletion.execution.execution_strategy.get_publisher")
@patch("src.requestcompletion.execution.execution_strategy.NodeState")
async def test_asyncio_execution_strategy_failure(mock_node_state, mock_get_publisher, mock_task, mock_publisher):
    mock_get_publisher.return_value = mock_publisher
    mock_task.invoke = AsyncMock(side_effect=RuntimeError("fail"))
    mock_node_state.return_value = "node-state"

    strat = AsyncioExecutionStrategy()
    response = await strat.execute(mock_task)

    assert isinstance(response, RequestFailure)
    assert isinstance(response.error, RuntimeError)
    assert response.node_state == "node-state"
    mock_publisher.publish.assert_awaited_once_with(response)
# ============ END AsyncioExecutionStrategy Failure Tests ===============

# ============ START AsyncioExecutionStrategy Shutdown Tests ===============
def test_asyncio_execution_strategy_shutdown_noop():
    strat = AsyncioExecutionStrategy()
    # Should not raise or do anything
    strat.shutdown()
# ============ END AsyncioExecutionStrategy Shutdown Tests ===============
