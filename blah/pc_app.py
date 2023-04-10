from typing import Callable, Any
import beaker
import os
import algokit_utils as au
from algosdk import abi
from algosdk.atomic_transaction_composer import (
    TransactionSigner,
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
    method = app_client._app_client.app_spec.contract.get_method_by_name(method_name)

    def _method_caller(_self: pc.State):
        state = _self.substates[method_name]
        args = state.dict()
        prepared_args: dict[str, Any] = {}
        for expected_args in method.args:
            if expected_args.name not in args:
                raise ValueError(
                    f"Missing argument {expected_args.name} for method {method_name}"
                )

            match expected_args.type:
                case abi.UintType():
                    prepared_args[expected_args.name] = int(args[expected_args.name])
                case abi.StringType():
                    prepared_args[expected_args.name] = str(args[expected_args.name])
                case _:
                    pass

        result = app_client.call(method_name, **prepared_args)  # type: ignore
        state.result = result.return_value

    _method_caller.__name__ = f"{method_name}_call"
    _method_caller.__qualname__ = f"{method_name}_call"
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

        self.AppState = self.app_state()
        self.action_states = self.get_action_states()

        env_name = f"{self.app_spec.contract.name}_APP_ID"
        if self.app_client.app_id == 0:
            if (env_app_id := os.getenv(env_name)) is not None:
                self.app_client.app_id = int(env_app_id)

        if auto_create and self.app_client.app_id == 0:
            app_id, _, _ = self.app_client.create()
            self.app_client.app_id = app_id
            os.environ[env_name] = str(app_id)

    @classmethod
    def from_app_spec(cls, path: str, app_id: int = 0) -> "PCApp":
        with open(path) as f:
            app_spec = au.ApplicationSpecification.from_json(f.read())
        acct = beaker.sandbox.get_accounts().pop()
        algod = beaker.sandbox.get_algod_client()
        app_client = beaker.client.ApplicationClient(
            algod, app_spec, signer=acct.signer, app_id=app_id
        )
        return cls(app_client)

    def app_state(self) -> type[pc.State]:
        fields = self.get_global_state_fields()
        return type("AppState", (pc.State,), fields)

    def get_action_states(self) -> dict[str, type[pc.State]]:
        states: dict[str, type[pc.State]] = {}
        for method in self.app_spec.contract.methods:
            if method.name == "create":
                continue

            fields = {
                f"{method.name}_call": method_caller(self.app_client, method.name)
            }
            MethodState = type(f"{method.name}", (self.AppState,), fields)

            for arg in method.args:
                if arg.name is None:
                    continue
                if arg.type is None:
                    continue

                MethodState.add_var(arg.name, int, 0)  # type: ignore

            if method.returns is not None:
                MethodState.add_var("result", str, "not called")  # type: ignore

            states[method.name] = MethodState

        return states

    def get_global_state_fields(self) -> dict[str, pc.Var]:
        fields: dict[str, pc.Var] = {}
        for k, v in self.app_spec.schema["global"]["declared"].items():
            fields[k] = state_val_getter(self.app_client, k, v)
        return fields

    def render_actions(self) -> list[pc.Component]:
        actions = []
        for method in self.app_spec.contract.methods:
            if method.name == "create":
                continue

            MethodState = self.action_states[method.name]

            arg_inputs = []
            for arg in method.args:
                if arg.name is None:
                    continue
                if arg.type is None:
                    continue

                arg_inputs.append(
                    pc.number_input(
                        default_value=getattr(MethodState, arg.name),
                        on_change=getattr(MethodState, f"set_{arg.name}"),
                    )
                )

            if method.returns is not None:
                arg_inputs.append(
                    pc.box(
                        pc.text(getattr(MethodState, "result")),
                        border_radius="1em",
                        bg="gray",
                        border_color="black",
                    )
                )

            action = pc.hstack(
                *arg_inputs,
                pc.button(
                    method.name,
                    border_radius="1em",
                    on_click=getattr(MethodState, f"{method.name}_call"),
                ),
            )

            actions.append(action)
        return actions

    def render_global_state(self) -> list[pc.Component]:
        global_state = []
        for k, v in self.app_spec.schema["global"]["declared"].items():
            gsv = pc.heading(f"{k} | " + getattr(self.AppState, k), font_size="2em")

            global_state.append(gsv)
        return global_state

    def dapp_flow_url(self) -> str:
        return (
            "https://app.dappflow.org/explorer/"
            f"application/{self.app_client.app_id}/transactions"
        )
