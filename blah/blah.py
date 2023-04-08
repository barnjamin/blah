from typing import Callable
import beaker
import os
import algokit_utils as au
import pynecone as pc


class PCApp:
    def __init__(
        self, app_client: beaker.client.ApplicationClient, create: bool = True
    ):
        self.account = (app_client.sender, app_client.signer)
        self.app_client = app_client
        self.app_spec = app_client._app_client.app_spec

        # Only create the app once
        if self.app_client.app_id == 0:
            if env_app_id := os.getenv("PC_APP_ID") is not None:
                self.app_client.app_id = int(env_app_id)
            elif create:
                app_id, _, _ = self.app_client.create()
                app_client.app_id = app_id
                os.environ["PC_APP_ID"] = str(app_id)

    @staticmethod
    def from_app_spec(path: str, app_id: int = 0) -> "PCApp":
        with open(path) as f:
            app_spec = au.ApplicationSpecification.from_json(f.read())
        acct = beaker.sandbox.get_accounts().pop()
        algod = beaker.sandbox.get_algod_client()
        app_client = beaker.client.ApplicationClient(
            algod, app_spec, signer=acct.signer, app_id=app_id
        )
        return PCApp(app_client)

    def get_state_fields(self) -> dict:
        def variable_getter(key: str, default_value) -> pc.Var:
            def _variable_getter(_self):
                return self.app_client.get_global_state().get(key, default_value)

            _variable_getter.__name__ = key
            _variable_getter.__qualname__ = key
            return pc.var(_variable_getter)

        def method_caller(method_name: str) -> Callable:
            def _method_caller(_self):
                self.app_client.call(method_name)

            _method_caller.__name__ = method.name
            _method_caller.__qualname__ = method.name
            return _method_caller

        fields: dict = {}
        for method in self.app_spec.contract.methods:
            if method.name == "create":
                continue
            fields[method.name] = method_caller(method.name)

        for k, v in self.app_spec.schema["global"]["declared"].items():
            fields[k] = variable_getter(
                key=k, default_value=0 if v["type"] == "uint64" else ""
            )

        return fields

    def get_actions(self) -> list:
        buttons = []
        for method in pcap.app_spec.contract.methods:
            if method.name == "create":
                continue
            buttons.append(
                pc.button(
                    method.name,
                    border_radius="1em",
                    on_click=getattr(State, method.name),
                )
            )
        return buttons

    def get_global_state(self) -> list:
        statevals = []
        for k, v in pcap.app_spec.schema["global"]["declared"].items():
            statevals.append(pc.heading(getattr(State, k), font_size="2em"))

        return statevals

    def get_local_state(self) -> list:
        statevals = []
        for k, v in pcap.app_spec.schema["local"]["declared"].items():
            statevals.append(pc.heading(getattr(State, k), font_size="2em"))

        return statevals

    def dapp_flow(self):
        return f"https://app.dappflow.org/explorer/application/{self.app_client.app_id}/transactions"


p = "blah/application/artifacts/application.json"
pcap = PCApp.from_app_spec(p)


def index():
    return pc.vstack(
        pc.hstack(*pcap.get_actions(), *pcap.get_global_state()),
        pc.link("DappFlow", href=pcap.dapp_flow(), is_external=True),
    )


State = type("State", (pc.State,), pcap.get_state_fields())
app = pc.App(state=State)
app.add_page(index)
app.compile()
