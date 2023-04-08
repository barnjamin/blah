from typing import Callable
import beaker
import os
import algokit_utils as au
import pynecone as pc

with open("blah/application/artifacts/application.json") as f:
    app_spec = au.ApplicationSpecification.from_json(f.read())

accts = beaker.sandbox.get_accounts()
acct = accts.pop()
algod = beaker.sandbox.get_algod_client()

app_client = beaker.client.ApplicationClient(algod, app_spec, signer=acct.signer)

# Only create the app once
if app_id := os.getenv("PC_APP_ID") is not None:
    app_client.app_id = int(app_id)
else:
    created_id, _, _ = app_client.create()
    os.environ["PC_APP_ID"] = str(created_id)


def variable_getter(key: str, default_value) -> pc.Var:
    def _variable_getter(self):
        return app_client.get_global_state().get(key, default_value)

    _variable_getter.__name__ = key
    return pc.var(_variable_getter)


def method_caller(method_name: str) -> Callable:
    def _method_caller(self):
        app_client.call(method_name)

    return _method_caller


fields: dict = {}
for method in app_spec.contract.methods:
    meth = method_caller(method.name)
    meth.__name__ = method.name
    meth.__qualname__ = method.name
    fields[method.name] = meth

for k, v in app_spec.schema["global"]["declared"].items():
    fields[k] = variable_getter(key=k, default_value=0 if v["type"] == "uint64" else "")

State = type("State", (pc.State,), fields)


dapp_flow = (
    f"https://app.dappflow.org/explorer/application/{app_client.app_id}/transactions"
)


def index():
    return pc.vstack(
        pc.hstack(
            pc.button(
                "Decrement",
                color_scheme="red",
                border_radius="1em",
                on_click=State.decrement,
            ),
            pc.heading(State.count, font_size="2em"),
            pc.button(
                "Increment",
                color_scheme="green",
                border_radius="1em",
                on_click=State.increment,
            ),
        ),
        pc.link("DappFlow", href=dapp_flow, is_external=True),
    )


app = pc.App(state=State)
app.add_page(index)
app.compile()
