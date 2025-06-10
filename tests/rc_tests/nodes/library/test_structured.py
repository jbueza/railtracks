import pytest
import requestcompletion as rc
from pydantic import BaseModel
from requestcompletion.exceptions import RCNodeCreationException
from typing import Type

# ================================================ START basic functionality =========================================================
# ================================================ END basic functionality ===========================================================


# ================================================ START Exception testing ===========================================================
# =================== START Easy Usage Node Creation ===================
@pytest.mark.asyncio
async def test_easy_usage_no_output_model():
    with pytest.raises(RCNodeCreationException, match="Output model cannot be empty"):
        _ = rc.library.structured_llm(
            output_model=None,
            system_message=rc.llm.SystemMessage(
                "You are a helpful assistant that can strucure the response into a structured output."
            ),
            model=rc.llm.OpenAILLM("gpt-4o"),
            pretty_name="Structured ToolCallLLM",
        )

@pytest.mark.asyncio
async def test_easy_usage_empty_output_model(empty_output_model):
    with pytest.raises(RCNodeCreationException, match="Output model cannot be empty"):
        _ = rc.library.structured_llm(
            output_model=empty_output_model,
            system_message=rc.llm.SystemMessage(
                "You are a helpful assistant that can strucure the response into a structured output."
            ),
            model=rc.llm.OpenAILLM("gpt-4o"),
            pretty_name="Structured ToolCallLLM",
        )

@pytest.mark.asyncio
async def test_easy_usage_tool_details_not_provided(simple_output_model):
    with pytest.raises(
        RCNodeCreationException,
        match="Tool parameters provided but no tool details provided.",
    ):
        _ = rc.library.structured_llm(
            output_model=simple_output_model,
            system_message=rc.llm.SystemMessage(
                "You are a helpful assistant that can strucure the response into a structured output."
            ),
            model=rc.llm.OpenAILLM("gpt-4o"),
            pretty_name="Structured ToolCallLLM",
            tool_params={
                rc.llm.Parameter(
                    name="text_input",
                    param_type="string",
                    description="A sentence to generate a response for.",
                )
            },
        )


@pytest.mark.asyncio
async def test_easy_usage_duplicate_parameter_names(simple_output_model):
    with pytest.raises(
        RCNodeCreationException, match="Duplicate parameter names are not allowed."
    ):
        _ = rc.library.structured_llm(
            output_model=simple_output_model,
            system_message=rc.llm.SystemMessage(
                "You are a helpful assistant that can strucure the response into a structured output."
            ),
            model=rc.llm.OpenAILLM("gpt-4o"),
            pretty_name="Structured ToolCallLLM",
            tool_details="A tool that generates a structured response that includes word count.",
            tool_params={
                rc.llm.Parameter(
                    name="text_input",
                    param_type="string",
                    description="A sentence to generate a response for.",
                ),
                rc.llm.Parameter(
                    name="text_input",
                    param_type="string",
                    description="A duplicate parameter.",
                ),
            },
        )


@pytest.mark.asyncio
async def test_easy_usage_system_message_is_a_string(simple_output_model):
    with pytest.raises(
        RCNodeCreationException,
        match="system_message must be a SystemMessage object, not a string or any other type.",
    ):
        _ = rc.library.structured_llm(
            output_model=simple_output_model,
            system_message="You are a helpful assistant that can strucure the response into a structured output.",
            model=rc.llm.OpenAILLM("gpt-4o"),
            pretty_name="Structured ToolCallLLM",
        )

# =================== END Easy Usage Node Creation ===================

# =================== START Class Based Node Creation ===================
@pytest.mark.asyncio
async def test_class_based_empty_output_model(empty_output_model):
    with pytest.raises(RCNodeCreationException, match="Output model cannot be empty"):
        class Structurer(rc.library.StructuredLLM):
            def __init__(
                self,
                message_history: rc.llm.MessageHistory,
                llm_model: rc.llm.ModelBase = None,
            ):
                message_history = [x for x in message_history if x.role != "system"]
                message_history.insert(0, rc.llm.SystemMessage("You are a helpful assistant."))
                super().__init__(
                    message_history=message_history,
                    llm_model=llm_model,
                )

            @classmethod
            def output_model(cls) -> Type[BaseModel]:
                return empty_output_model
            
            @classmethod
            def pretty_name(cls) -> str:
                return "Structurer"

@pytest.mark.asyncio
async def test_class_based_output_model_not_class_based(simple_output_model):
    with pytest.raises(RCNodeCreationException, match="The 'output_model' method must be a @classmethod."):
        class Structurer(rc.library.StructuredLLM):
            def __init__(
                self,
                message_history: rc.llm.MessageHistory,
                llm_model: rc.llm.ModelBase = None,
            ):
                message_history = [x for x in message_history if x.role != "system"]
                message_history.insert(0, rc.llm.SystemMessage("You are a helpful assistant."))
                super().__init__(
                    message_history=message_history,
                    llm_model=llm_model,
                )

            def output_model(cls) -> Type[BaseModel]:
                return simple_output_model
            
            @classmethod
            def pretty_name(cls) -> str:
                return "Structurer"
            
@pytest.mark.asyncio
async def test_class_based_output_model_not_pydantic():
    with pytest.raises(RCNodeCreationException, match="Output model cannot be empty/must be a pydantic model"):
        class Structurer(rc.library.StructuredLLM):
            def __init__(
                self,
                message_history: rc.llm.MessageHistory,
                llm_model: rc.llm.ModelBase = None,
            ):
                message_history = [x for x in message_history if x.role != "system"]
                message_history.insert(0, rc.llm.SystemMessage("You are a helpful assistant."))
                super().__init__(
                    message_history=message_history,
                    llm_model=llm_model,
                )

            @classmethod
            def output_model(cls):
                return {"text": "hello world"}
            
            @classmethod
            def pretty_name(cls) -> str:
                return "Structurer"
# =================== END Class Based Node Creation =====================
# ================================================ END Exception testing =============================================================
