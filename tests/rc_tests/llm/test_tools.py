from railtownai_rc.llm import Parameter, Tool


def test_create_parameter():
    p = Parameter(
        name="test",
        param_type="string",
    )

    assert p.name == "test"
    assert p.param_type == "string"
    assert p.description == ""
    assert p.required == True


def test_simple_one_param_function():
    p = Parameter(
        name="test",
        param_type="string",
    )

    pydantic_type = Tool.convert_params_to_model("test_func", {p})

    assert "test" in pydantic_type.model_json_schema()["properties"]

    t = Tool(name="test_func", detail="test", parameters={p})
    assert t.detail == "test"
    assert t.name == "test_func"
    assert t.parameters.model_json_schema() == pydantic_type.model_json_schema()
    assert str(t) == f"Tool(name=test_func, detail=test, parameters={pydantic_type.model_json_schema()})"
