import pytest
from copy import deepcopy
import src.requestcompletion as rc
from tests.rc_tests.fixtures.nodes import ActionType, CapitalizeText, FatalErrorNode, UnknownErrorNode, TimeoutNode
from pydantic import BaseModel, Field

@pytest.fixture
def model():
    return rc.llm.OpenAILLM("gpt-4o")

@pytest.fixture
def terminal_llms_system_messages():
    system_rng = rc.llm.SystemMessage("You are a random integer generator that will return a random list of integers between 0 and 100. Do not return more than 10 integers.")
    system_rng_operation = rc.llm.SystemMessage("You are a random mathematical operation calculator that will apply a random operation to the list of integers that will be provided by the user and return the result. The answer should be only a single integer.")
    system_math_genius = rc.llm.SystemMessage("You are a math genius that will get a list of integers(loi) and another interger(x), your task is to predict what operation must be appled to the list of integers to get the result of x.")
    
    return system_rng, system_rng_operation, system_math_genius

@pytest.fixture
def sttructured_llms_system_messages():
    system_undergrad_student = rc.llm.SystemMessage("You are an undergraduate university student. You are taking a math class where you need tto write proofs. Be concise and to the point.")
    system_professor = rc.llm.SystemMessage("You are a senior Math professor at a university. You need to grade the students work (scale of 0 to 100) and give a reasoning for the grading.")

    return system_undergrad_student, system_professor

@pytest.fixture
def terminal_nodes(request, model, terminal_llms_system_messages):
    """
    Returns the appropriate nodes based on the parametrized fixture name.
    """
    fixture_name = request.param
    system_rng, system_rng_operation, system_math_genius = terminal_llms_system_messages
    
    if fixture_name == "easy_wrapper":
        rng_node = rc.library.terminal_llm(pretty_name="RNG Node", system_message=system_rng, model=model)     
        rng_operation_node = rc.library.terminal_llm(pretty_name="RNG Operation Node", system_message=system_rng_operation, model=model)
        math_detective_node = rc.library.terminal_llm(pretty_name="Math Detective Node", system_message=system_math_genius, model=model)
        
        return rng_node, rng_operation_node, math_detective_node
        
    elif fixture_name == "class_based":
        def make_terminal_llm_class_version(pretty_name: str, system_message: rc.llm.SystemMessage):
            class TerminalLLMNode(rc.library.TerminalLLM):
                def __init__(
                    self,
                    message_history: rc.llm.MessageHistory,
                    llm_model: rc.llm.ModelBase,
                ):
                    message_history = [x for x in message_history if x.role != "system"]
                    message_history.insert(0, system_message)
                    super().__init__(message_history=message_history, model=llm_model)

                def pretty_name(self) -> str:
                    return pretty_name
            
            return TerminalLLMNode

        rng_node = make_terminal_llm_class_version("RNG Node", system_message=system_rng)   
        rng_operation_node = make_terminal_llm_class_version("RNG Operation Node", system_message=system_rng_operation)
        math_detective_node = make_terminal_llm_class_version("Math Detective Node", system_message=system_math_genius)
        
        return rng_node, rng_operation_node, math_detective_node
    
    else:
        raise ValueError(f"Unknown node fixture: {fixture_name}")

@pytest.fixture
def structured_nodes(request, model, sttructured_llms_system_messages):
    """
    Returns the appropriate nodes based on the parametrized fixture name.
    """
    fixture_name = request.param
    system_undergrad_student, system_professor = sttructured_llms_system_messages
    class ProofModel(BaseModel):
        proof: str = Field(description="The mathematical proof of the statement")

    class GradingSchema(BaseModel):
        overall_score: float = Field(description="The grade on the proof on a scale of 0 to 100")
        feedback: str = Field(description="Any suggestions on improving the proof or reason for the grade")

    if fixture_name == "easy_wrapper":
        math_undergrad_student_node = rc.library.structured_llm(pretty_name="Math Undergraduate Student Node", output_model=ProofModel, system_message=system_undergrad_student, model=model)
        math_professor_node = rc.library.structured_llm(pretty_name="Math Professor Node", output_model=GradingSchema, system_message=system_professor, model=model)
        
        return math_undergrad_student_node, math_professor_node
        
    elif fixture_name == "class_based":
        def make_structured_llm_class_version(pretty_name: str, system_message: rc.llm.SystemMessage, output_model: BaseModel):
            class StructuredLLMNode(rc.library.StructuredLLM):
                def __init__(
                    self,
                    message_history: rc.llm.MessageHistory,
                    llm_model: rc.llm.ModelBase,
                ):
                    message_history = [x for x in message_history if x.role != "system"]
                    message_history.insert(0, system_message)
                    super().__init__(message_history=message_history, model=llm_model)

                def output_model(self) -> BaseModel:
                    return output_model
                
                def pretty_name(self) -> str:
                    return pretty_name
            
            return StructuredLLMNode

        math_undergrad_student_node = make_structured_llm_class_version("Math Undergraduate Student Node", output_model=ProofModel, system_message=system_undergrad_student)   
        math_professor_node = make_structured_llm_class_version("Math Professor Node", output_model=GradingSchema, system_message=system_professor)
        
        return math_undergrad_student_node, math_professor_node
    
    else:
        raise ValueError(f"Unknown node fixture: {fixture_name}")
    

@pytest.mark.asyncio
@pytest.mark.parametrize("terminal_nodes", ["class_based", "easy_wrapper"], indirect=True)
async def test_message_history_not_mutated_terminal_llm(model, terminal_nodes):
    """
    Verify that message history is not modified after rc.call when passed to nodes constructed using different methods.
    """
    rng_node, rng_operation_node, math_detective_node = terminal_nodes
    
    # Determine if we need to pass the model based on which fixture was used
    needs_model = isinstance(terminal_nodes, tuple) and any(hasattr(node, '__call__') and node.__name__ == "TerminalLLMNode" for node in terminal_nodes)

    async def make_math_game_node(message_history: rc.llm.MessageHistory):
        original_message_history = deepcopy(message_history)

        # Common parameters for node calls
        call_params = {"message_history": message_history}
        if needs_model:
            call_params["llm_model"] = model

        # First node call
        random_num_list_response = await rc.call(rng_node, **call_params)
        assert all(orig.content == new.content for orig, new in zip(original_message_history, message_history)), "Message history modified after rc.call 1"

        message_history.append(rc.llm.AssistantMessage("The list of random integer: " + str(random_num_list_response)))
        original_message_history.append(rc.llm.AssistantMessage("The list of random integer: " + str(random_num_list_response)))

        # Second node call
        operation_response = await rc.call(rng_operation_node, **call_params)
        assert all(orig.content == new.content for orig, new in zip(original_message_history, message_history)), "Message history modified after rc.call 2"

        message_history.append(rc.llm.AssistantMessage("The result int (x) = " + str(operation_response)))
        original_message_history.append(rc.llm.AssistantMessage("The result int (x) = " + str(operation_response)))

        # Third node call
        response = await rc.call(math_detective_node, **call_params)
        assert all(orig.content == new.content for orig, new in zip(original_message_history, message_history)), "Message history modified after rc.call 3"

        return response

    MathGameNode = rc.library.from_function(make_math_game_node)

    with rc.Runner() as runner:
        message_history = rc.llm.MessageHistory([rc.llm.UserMessage("You can start the game")])
        original_message_history = deepcopy(message_history)
        _ = await runner.run(MathGameNode, message_history=message_history)
        assert all(orig.content == new.content for orig, new in zip(original_message_history, message_history)), "Message history modified after runner run"


@pytest.mark.asyncio
@pytest.mark.parametrize("structured_nodes", ["class_based", "easy_wrapper"], indirect=True)
async def test_message_history_not_mutated_structured_llm(model, structured_nodes):
    """
    Verify that message history is not modified after rc.call when passed to nodes constructed using different methods.
    """
    math_undergrad_student_node, math_professor_node = structured_nodes
    
    # Determine if we need to pass the model based on which fixture was used
    needs_model = isinstance(structured_nodes, tuple) and any(hasattr(node, '__call__') and node.__name__ == "StructuredLLMNode" for node in structured_nodes)

    async def math_proof_node(message_history: rc.llm.MessageHistory):
        original_message_history = deepcopy(message_history)

        # Common parameters for node calls
        call_params = {"message_history": message_history}
        if needs_model:
            call_params["llm_model"] = model

        # First node (math student node)
        student_proof = await rc.call(math_undergrad_student_node, **call_params)
        assert all(orig.content == new.content for orig, new in zip(original_message_history, message_history)), "Message history modified after rc.call 1"

        message_history.append(rc.llm.AssistantMessage("The proof: " + student_proof.proof))
        original_message_history.append(rc.llm.AssistantMessage("The proof: " + student_proof.proof))

        # Second node call (math professor node)
        prof_grade = await rc.call(math_professor_node, **call_params)
        assert all(orig.content == new.content for orig, new in zip(original_message_history, message_history)), "Message history modified after rc.call 2"

        message_history.append(rc.llm.AssistantMessage("The grade: " + str(prof_grade.overall_score)))
        message_history.append(rc.llm.AssistantMessage("The feedback: " + prof_grade.feedback))
        original_message_history.append(rc.llm.AssistantMessage("The grade: " + str(prof_grade.overall_score)))
        original_message_history.append(rc.llm.AssistantMessage("The feedback: " + prof_grade.feedback))

        return prof_grade

    MathProofNode = rc.library.from_function(math_proof_node)

    with rc.Runner() as runner:
        message_history = rc.llm.MessageHistory([rc.llm.UserMessage("Prove that the sum of all numbers until infinity is -1/12")])
        original_message_history = deepcopy(message_history)
        _ = await runner.run(MathProofNode, message_history=message_history)
        assert all(orig.content == new.content for orig, new in zip(original_message_history, message_history)), "Message history modified after runner run"