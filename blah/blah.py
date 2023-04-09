import json
from typing import Callable, cast
import beaker
import functools
import os
import algokit_utils as au
from algosdk import transaction
from algosdk.atomic_transaction_composer import (
    TransactionSigner,
    AtomicTransactionComposer,
)
import pynecone as pc


class TxnVar(pc.Base):
    sender: str = ""
    receiver: str = ""
    amount: int = 0
    asset_id: int = 0


def method_caller(
    app_client: beaker.client.ApplicationClient, method_name: str
) -> Callable:
    def _method_caller(_self):
        state_dict = _self.dict()
        args: dict = {}

        for sk, sv in state_dict.items():
            if sk.startswith(method_name):
                args = sv

        prepared_args = {}
        method = app_client._app_client.app_spec.contract.get_method_by_name(method_name)
        for expected_args in method.args:
            if expected_args.name not in args:
                raise ValueError(
                    f"Missing argument {expected_args.name} for method {method_name}"
                )

            if str(expected_args.type) == "uint64":
                prepared_args[expected_args.name] = int(args[expected_args.name])

        result = app_client.call(method_name, **prepared_args)
        print(result.return_value)

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
        self.sender: str = app_client.get_sender()
        self.signer: TransactionSigner = app_client.get_signer()

        self.app_client = app_client
        self.app_spec = app_client._app_client.app_spec

        env_name = f"{self.app_spec.contract.name}_APP_ID"
        if self.app_client.app_id == 0:
            if env_app_id := os.getenv(env_name) is not None:
                self.app_client.app_id = int(env_app_id)

        if auto_create:
            app_id, _, _ = self.app_client.create()
            self.app_client.app_id = app_id
            os.environ[env_name] = str(app_id)

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
        return type("AppState", (pc.State,), fields)

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

    def get_actions(self, ctx: type[pc.State]) -> list[dict]:
        """Generate a list of action components and their associated state.
        Used to call methods on the app and update the state.

        Args:
            ctx (type[pc.State]): The state class to use for the action

        Returns:
            list[dict]: A list of action components and their associated state
        """

        actions = []
        for method in pcap.app_spec.contract.methods:
            if method.name == "create":
                continue

            MethodState = type(f"{method.name}MethodState", (ctx,), {})

            arg_values: dict = {}
            arg_inputs = []
            for arg in method.args:
                if arg.name is None:
                    continue
                if arg.type is None:
                    continue

                MethodState.add_var(arg.name, int, 0)  # type: ignore

                arg_inputs.append(
                    pc.number_input(
                        default_value=getattr(MethodState, arg.name),
                        on_change=getattr(MethodState, f"set_{arg.name}"),
                    )
                )
                arg_values[arg.name] = getattr(MethodState, arg.name)

                # if str(arg.type) in ("pay", "axfer"):
                #    MethodState.add_var(
                #        arg.name,
                #        TxnVar,
                #        TxnVar(
                #            sender=self.sender,
                #            receiver=self.sender,
                #            amount=0,
                #            asset_id=0,
                #        ),
                #    )

                #    args.append(
                #        pc.number_input(
                #            default_value=getattr(MethodState, arg.name).amount,
                #        )
                #    )

            action = pc.hstack(
                *arg_inputs,
                pc.button(
                    method.name,
                    border_radius="1em",
                    on_click=getattr(AppState, method.name),
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


counter_path = "blah/application/artifacts/application.json"
amm_path = "/home/ben/beaker/examples/amm/ConstantProductAMM.artifacts/application.json"
calculator_path = (
    "/home/ben/beaker/examples/simple/Calculator.artifacts/application.json"
)
pcap = PCApp.from_app_spec(calculator_path)
AppState = pcap.app_state()


def index():
    return pc.vstack(
        *pcap.get_actions(AppState),
        *pcap.get_global_state(),
        pc.link("DappFlow", href=pcap.dapp_flow(), is_external=True),
    )


app = pc.App(state=AppState)
app.add_page(index)
app.compile()
