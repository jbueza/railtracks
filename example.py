import requestcompletion as rc
import litellm


model = rc.llm.GeminiLLM(model_name="gemini-pro")


mh = rc.llm.MessageHistory(
    [
        rc.llm.SystemMessage("You are a helpful AI writing assistant."),
        rc.llm.UserMessage("Hello, how are you?"),
    ]
)

# resp = model.chat(mh)

resp = litellm.completion(
    model="gemini/gemini-pro", 
    messages=[{"role": "user", "content": "write code for saying hi from LiteLLM"}]
)
print(resp)