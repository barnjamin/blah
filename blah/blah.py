import functools
from typing import Callable
import beaker
import os
import algokit_utils as au
import algosdk
import pynecone as pc


def method_caller(
    app_client: beaker.client.ApplicationClient, method_name: str
) -> Callable:
    def _method_caller(_self, *args, **kwargs):
        app_client.call(method_name, *args, **kwargs)

    _method_caller.__name__ = method_name
    _method_caller.__qualname__ = method_name
    return _method_caller


def state_val_getter(
    app_client: beaker.client.ApplicationClient, key: str, val: dict
) -> pc.Var:
    def _variable_getter(_self):
        # TODO: get this once for all state
        return app_client.get_global_state().get(
            key, 0 if val["type"] == "uint64" else ""
        )

    _variable_getter.__name__ = key
    _variable_getter.__qualname__ = key
    return pc.var(_variable_getter)


class PCApp:
    def __init__(
        self, app_client: beaker.client.ApplicationClient, auto_create: bool = True
    ):
        self.account = (app_client.sender, app_client.signer)
        self.app_client = app_client
        self.app_spec = app_client._app_client.app_spec

        if self.app_client.app_id == 0:
            if env_app_id := os.getenv("PC_APP_ID") is not None:
                self.app_client.app_id = int(env_app_id)
            elif auto_create:
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

    def app_state(self) -> type[pc.State]:
        fields = pcap.get_states() | pcap.get_action_states()
        return type("ok", (pc.State,), fields)

    def get_states(self) -> dict:
        fields: dict = {}
        for k, v in self.app_spec.schema["global"]["declared"].items():
            fields[k] = state_val_getter(self.app_client, k, v)
        return fields

    def get_action_states(self) -> dict:
        fields: dict = {}
        for method in self.app_spec.contract.methods:
            if method.name == "create":
                continue
            fields[method.name] = method_caller(self.app_client, method.name)

        return fields

    def get_actions(self, ctx: type[pc.State]) -> list:
        actions = []
        for method in pcap.app_spec.contract.methods:
            if method.name == "create":
               continue

            args_key = f"{method.name}.args"
            fields = {
               args_key: [a.dictify() for a in method.args],
            }

            MethodState = type("MethodState", (ctx,), fields)

            def tx_input(arg):
                print(arg.__dict__)
                return pc.input(
                        placeholder=arg["name"],
                        #_type= "int" if str(arg.type) == "uint64" else "str",
                        width="100%",
                        outline="black",
                    )

            args = pc.foreach(getattr(MethodState, args_key), tx_input)

            send_tx = functools.partial(getattr(AppState, method.name), )
            
            action = pc.hstack(
                args,
                pc.button(
                    method.name,
                    border_radius="1em",
                    on_click=send_tx,
                ),
            )

            actions.append(action)
        return actions

    def get_global_state(self) -> list:
        global_state = []
        for k, v in pcap.app_spec.schema["global"]["declared"].items():
            gsv = pc.heading(f"{k} | " + getattr(AppState, k), font_size="2em")

            global_state.append(gsv)
        return global_state

    def get_local_state(self) -> list:
        local_state = []
        for k, v in pcap.app_spec.schema["local"]["declared"].items():
            local_state.append(pc.heading(getattr(AppState, k), font_size="2em"))
        return local_state

    def dapp_flow(self):
        return f"https://app.dappflow.org/explorer/application/{self.app_client.app_id}/transactions"


## p = "blah/application/artifacts/application.json"
p = "/home/ben/beaker/examples/amm/ConstantProductAMM.artifacts/application.json"
pcap = PCApp.from_app_spec(p)
AppState = pcap.app_state()

def index():
    return pc.vstack(
        *pcap.get_actions(AppState),
        *pcap.get_global_state(),
        pc.link("DappFlow", href=pcap.dapp_flow(), is_external=True),
    )

#class State(pc.State):
#    x: int = 123
#
#class ChildState(State):
#    x: int = 456
#

#def index():
#    return pc.vstack(
#        pc.heading(ChildState.x, font_size="2em"),
#    )

app = pc.App(state=AppState)
app.add_page(index)
app.compile()
