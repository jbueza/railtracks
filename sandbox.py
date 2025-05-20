import concurrent.futures
import contextvars

parent_id = contextvars.ContextVar("parent_id", default=None)
state_obj = contextvars.ContextVar("state_obj", default={})

buffer = []


def thread_action(new_parent_id, new_state_obj):

    buffer.append(f"1. parent_id: {parent_id.get()}, state_obj: {state_obj.get()}, id={new_parent_id}")
    parent_id.set(new_parent_id)

    new_dict = state_obj.get()
    new_dict.update(new_state_obj)
    state_obj.set(new_dict)
    buffer.append(f"2. parent_id: {parent_id.get()}, state_obj: {state_obj.get()}, id={new_parent_id}")
    return True


with concurrent.futures.ThreadPoolExecutor() as executor:
    rs = executor.map(
        thread_action,
        [1, 2, 3, 4, 5],
        [{"id": 1}, {"id": 2}, {"id": 3}, {"id": 4}, {"id": 5}],
    )

    for r in rs:
        print(r)

    print("\n".join(buffer))
