import time

ref = time.time()

import requestcompletion as rc

print("Time taken to import requestcompletion:", time.time() - ref)

ref = time.time()


class SimpleThinker(rc.library.TerminalLLM):
    @classmethod
    def pretty_name(cls) -> str:
        pass

    def __init__(self, query: str):
        super().__init__(
            message_history=rc.llm.MessageHistory(
                [
                    rc.llm.SystemMessage(
                        "You are a helpful asssinatnt with a simple mind that supplies simple solutions to any question. "
                    ),
                    rc.llm.UserMessage(query),
                ]
            ),
            model=rc.llm.OpenAILLM("gpt-4o"),
        )


print("Time taken to define SimpleThinker:", time.time() - ref)

ref = time.time()
with rc.Runner() as run:
    print("Time taken to run SimpleThinker:", time.time() - ref)
    ref = time.time()
    print(run.run_sync(SimpleThinker, "How should I add 2 number together").answer)
    print("Time taken to run SimpleThinker:", time.time() - ref)
