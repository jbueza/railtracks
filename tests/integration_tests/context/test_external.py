import requestcompletion as rc
from requestcompletion.context import put, get
from requestcompletion.nodes.library import from_function
from requestcompletion.interaction.call import call


def set_context():
    put("test_key", "test_value")


def retrieve_context():
    return get("test_key", default="default_value")


async def context_flow():
    await call(from_function(set_context))
    return await call(from_function(retrieve_context))


def test_put_context():
    context_node = from_function(context_flow)
    with rc.Runner() as runner:
        result = runner.run_sync(context_node)

    assert result.answer == "test_value"
