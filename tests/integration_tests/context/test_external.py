import requestcompletion as rc
from requestcompletion.context import put, get
from requestcompletion.nodes.library import from_function, terminal_llm
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


def test_prompt_injection():
    prompt = "The secret message is: {secret_value}"
    message_history = rc.llm.MessageHistory([
        rc.llm.UserMessage("What is the secret message? Only return the message.")
    ])

    node = terminal_llm(system_message=prompt, model=rc.llm.OpenAILLM("gpt-4o"))

    with rc.Runner(context={"secret_value": "'tomato'"}) as runner:
        response = runner.run_sync(node, message_history)

    assert response.answer == "tomato"
