import pytest
import requestcompletion as rc

from pydantic import BaseModel, Field
from requestcompletion.exceptions import NodeCreationError

NODE_INIT_METHODS = ["easy_wrapper", "class_based"]


@pytest.mark.asyncio
@pytest.mark.parametrize("simple_node", NODE_INIT_METHODS, indirect=True)
async def test_structured_with_no_tool_calls(simple_node, simple_output_model):
    """Test basic functionality of returning a structured output."""
    with rc.Runner(executor_config=rc.ExecutorConfig(logging_setting="NONE")) as runner:
        message_history = rc.llm.MessageHistory(
            [rc.llm.UserMessage("Generate a simple text and number.")]
        )
        response = await runner.run(simple_node, message_history=message_history)
        assert isinstance(response.answer, simple_output_model)
        assert isinstance(response.answer.text, str)
        assert isinstance(response.answer.number, int)

@pytest.mark.asyncio
@pytest.mark.skip("Skipping test due to stochastic LLM failures.")
async def test_tool_with_structured_output_child_tool():
    """Test a tool that uses another LLM tool with structured output as input."""

    # Define a structured output model
    class ChildResponse(BaseModel):
        message: str
        word_count: int

    class ParentResponse(BaseModel):
        message: str
        word_count: int
        success: bool

    # Define the child tool with structured output
    child_tool = rc.library.structured_llm(
        output_model=ChildResponse,
        system_message=rc.llm.SystemMessage(
            "You are a word counting tool that counts the number of words in the request provided by the user."
        ),
        model=rc.llm.OpenAILLM("gpt-4o"),
        pretty_name="Structured Child Tool",
        tool_details="A tool that generates a structured response that includes word count.",
        tool_params={
            rc.llm.Parameter(
                name="request",
                param_type="string",
                description="A sentence to generate a response for.",
            )
        },
    )

    # Define the parent tool that uses the child tool
    parent_tool = rc.library.tool_call_llm(
        output_model=ParentResponse,
        connected_nodes={child_tool},
        pretty_name="Parent Tool",
        system_message=rc.llm.SystemMessage(
            "Use the child tool to generate a structured response. Respond with the output from the child tool only. No additional text."
        ),
        model=rc.llm.OpenAILLM("gpt-4o"),
    )

    # Run the parent tool
    with rc.Runner(
        executor_config=rc.ExecutorConfig(logging_setting="NONE", timeout=1000)
    ) as runner:
        message_history = rc.llm.MessageHistory(
            [rc.llm.UserMessage("Generate a structured response for 'Hello World'.")]
        )
        response = await runner.run(parent_tool, message_history=message_history)

    # Assertions
    assert response.answer is not None
    assert isinstance(response.answer, ParentResponse)
    assert response.answer.message == "Hello World"
    assert response.answer.word_count == 2
    assert response.answer.success is True


# Not using the ones in conftest.py because we will have to use lazy_fixtures for that. lazy_fixture is not very well supported in pytest (better to avaoid it)
class SimpleOutput(BaseModel):
    text: str = Field(description="The text to return")


@pytest.mark.parametrize(
    "llm_function, connected_nodes",
    [
        (rc.library.tool_call_llm, {rc.library.from_function(lambda: "test")}),
        (rc.library.structured_llm, None),
    ],
    ids=["tool_call_llm", "structured_llm"],
)
@pytest.mark.parametrize(
    "output_model, tool_details, tool_params, expected_exception, match",
    [
        # Test: tool_params provided but tool_details is missing
        (
            SimpleOutput,
            None,
            [
                rc.llm.Parameter(
                    name="param1", param_type="string", description="A test parameter."
                )
            ],
            NodeCreationError,
            "Tool parameters are provided, but tool details are missing.",
        ),
        # Test: Duplicate parameter names in tool_params
        (
            SimpleOutput,
            "A test tool",
            [
                rc.llm.Parameter(
                    name="param1", param_type="string", description="A test parameter."
                ),
                rc.llm.Parameter(
                    name="param1",
                    param_type="string",
                    description="A duplicate parameter.",
                ),
            ],
            NodeCreationError,
            "Duplicate parameter names are not allowed.",
        ),
    ],
)
def test_structured_llm_tool_errors(
    output_model,
    tool_details,
    tool_params,
    llm_function,
    connected_nodes,
    expected_exception,
    match,
):
    kwargs = {
        "output_model": output_model,
        "tool_details": tool_details,
        "tool_params": tool_params,
    }
    if connected_nodes is not None:
        kwargs["connected_nodes"] = connected_nodes

    with pytest.raises(expected_exception, match=match):
        llm_function(**kwargs)


@pytest.mark.asyncio
async def test_functions_passed_tool_calls(only_function_taking_travel_planner_node, travel_planner_output_model):
    """Test the functionality of a ToolCallLLM node (using actual tools) with a structured output model."""
    with rc.Runner(executor_config=rc.ExecutorConfig(timeout=50, logging_setting="QUIET")) as runner:
        message_history = rc.llm.MessageHistory(
            [
                rc.llm.UserMessage(
                    "I live in Delhi. I am going to travel to Denmark for 3 days, followed by Germany for 2 days and finally New York for 4 days. Please provide me with a budget summary for the trip in INR."
                )
            ]
        )
        response = await runner.run(only_function_taking_travel_planner_node, message_history=message_history)
        assert isinstance(response.answer, travel_planner_output_model)
        assert isinstance(response.answer.travel_plan, str)
        assert isinstance(response.answer.Total_cost, float)
        assert isinstance(response.answer.Currency, str)

@pytest.mark.asyncio
@pytest.mark.parametrize("math_node", NODE_INIT_METHODS, indirect=True)
async def test_structured_with_terminal_llm_as_tool(math_node, math_output_model):
    """Test the functionality of a ToolCallLLM node (using terminalLLM as tool) with a structured output model."""
    with rc.Runner(executor_config=rc.ExecutorConfig(logging_setting="NONE")) as runner:
        message_history = rc.llm.MessageHistory(
            [rc.llm.UserMessage("Start the Math node.")]
        )
        response = await runner.run(math_node, message_history=message_history)
        assert isinstance(response.answer, math_output_model)
        assert isinstance(response.answer.sum, float)
        assert isinstance(response.answer.random_numbers, list)


@pytest.mark.asyncio
@pytest.mark.parametrize("complex_node", NODE_INIT_METHODS, indirect=True)
async def test_structured_with_complex_output_model(
    complex_node, person_output_model, simple_output_model
):
    """Test the functionality of structured output model with complex output model."""
    with rc.Runner(executor_config=rc.ExecutorConfig(logging_setting="NONE")) as runner:
        message_history = rc.llm.MessageHistory(
            [
                rc.llm.UserMessage(
                    "My name is John Doe. I am 30 years old. My favourite text is 'Hello World' and my favourite number is 1290."
                )
            ]
        )
        response = await runner.run(complex_node, message_history=message_history)
        assert isinstance(response.answer, person_output_model)
        assert isinstance(response.answer.name, str)
        assert isinstance(response.answer.age, int)
        assert isinstance(response.answer.Favourites, simple_output_model)
        assert isinstance(response.answer.Favourites.text, str)
        assert isinstance(response.answer.Favourites.number, int)


@pytest.mark.asyncio  # can remove this test once we have support for output_model with output_type = MessageHistory. See Line 30 in src/requestcompletion/nodes/library/easy_usage_wrappers/tool_call_llm.py
async def test_structured_tool_call_with_output_model_and_output_type(
    model, math_output_model
):
    """Tool call llm init with output model and output_type = message_history should raise an error."""
    rng_node = rc.library.terminal_llm(
        pretty_name="RNG Tool",
        system_message=rc.llm.SystemMessage(
            "You are a helful assistant that can generate 5 random numbers between 1 and 100."
        ),
        model=model,
        tool_details="A tool used to generate 5 random integers between 1 and 100.",
        tool_params=None,
    )

    with pytest.raises(
        NotImplementedError,
        match="MessageHistory output type is not supported with output_model at the moment.",
    ):
        _ = rc.library.tool_call_llm(
            connected_nodes={rng_node},
            pretty_name="Math Node",
            system_message=rc.llm.SystemMessage(
                "You are a math genius that calls the RNG tool to generate 5 random numbers between 1 and 100 and gives the sum of those numbers."
            ),
            model=model,
            output_type="MessageHistory",
            output_model=math_output_model,
        )



@pytest.mark.asyncio
@pytest.mark.parametrize("travel_planner_node", NODE_INIT_METHODS, indirect=True)
async def test_structured_with_tool_calls(
    travel_planner_node, travel_planner_output_model
):
    """Test the functionality of a ToolCallLLM node (using actual tools) with a structured output model."""
    with rc.Runner(
        executor_config=rc.ExecutorConfig(timeout=50, logging_setting="NONE")
    ) as runner:
        message_history = rc.llm.MessageHistory(
            [
                rc.llm.UserMessage(
                    "I live in Delhi. I am going to travel to Denmark for 3 days, followed by Germany for 2 days and finally New York for 4 days. Please provide me with a budget summary for the trip in INR."
                )
            ]
        )

        response = await runner.run(
            travel_planner_node, message_history=message_history
        )
        assert isinstance(response.answer, travel_planner_output_model)
        assert isinstance(response.answer.travel_plan, str)
        assert isinstance(response.answer.Total_cost, float)
        assert isinstance(response.answer.Currency, str)