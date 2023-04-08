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


class State(pc.State):
    app_id: int = app_client.app_id

    @pc.var
    def count(self):
        return app_client.get_global_state().get("count", 0)

    def increment(self):
        app_client.call("increment")

    def decrement(self):
        app_client.call("decrement")


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
