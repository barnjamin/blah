from typing import Callable, cast
import beaker
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
        return pc.window_alert("Hello world")
        for ss in _self.get_substates():
            if ss.get_name() == method_name:
                print(ss)
                print(dir(ss))
                print(ss.__dict__)

                print(_self)
                print(dir(_self))
                print(_self.__dict__)

                # _self.set__result(123)
                _self._result = 123
                print(_self.backend_vars)
                _self.mark_dirty()
                print(_self.__dict__)

        # prepared_args = {}
        # method = app_client._app_client.app_spec.contract.get_method_by_name(
        #    method_name
        # )
        # for expected_args in method.args:
        #    if expected_args.name not in args:
        #        raise ValueError(
        #            f"Missing argument {expected_args.name} for method {method_name}"
        #        )

        #    if str(expected_args.type) == "uint64":
        #        prepared_args[expected_args.name] = int(args[expected_args.name])

        # result = app_client.call(method_name, **prepared_args)

        # for ss in _self.get_substates():
        #    if ss.get_name() == method_name:
        #        print("Setting result")
        #        print(ss._result)
        #        print(result.return_value)
        #        print(ss)
        #        print(dir(ss))
        #        print(ss.__dict__)

        #        ss.result = result.return_value
        #        _self.mark_dirty()
        #    #_self.set_result(str(result.return_value))

        # _self.get_substate(method_name).set_result(result.return_value)
        # print(_self)
        # print(dir(_self))
        # print(_self.__dict__)
        # getattr(_self, f"{method_name}").set_result(result.return_value)
        # print(result.return_value)

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
        fields = self.get_states()
        return type("AppState", (pc.State,), fields)

    def get_states(self) -> dict:
        fields: dict = {}
        for k, v in self.app_spec.schema["global"]["declared"].items():
            fields[k] = state_val_getter(self.app_client, k, v)
        return fields

    def get_actions(self) -> list[dict]:
        """Generate a list of action components and their associated state.
        Used to call methods on the app and update the state.

        Args:
            ctx (type[pc.State]): The state class to use for the action

        Returns:
            list[dict]: A list of action components and their associated state
        """

        actions = []
        for method in self.app_spec.contract.methods:
            if method.name == "create":
                continue

            fields = {
                f"{method.name}_call": method_caller(self.app_client, method.name)
            }
            MethodState = type(f"{method.name}", (self.AppState,), fields)

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

            if method.returns is not None:
                MethodState.add_var("_result", str, "not called")  # type: ignore
                arg_inputs.append(
                    pc.box(
                        pc.text(getattr(MethodState, "_result")),
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

    def get_global_state(self) -> list:
        global_state = []
        for k, v in self.app_spec.schema["global"]["declared"].items():
            gsv = pc.heading(f"{k} | " + getattr(self.AppState, k), font_size="2em")

            global_state.append(gsv)
        return global_state

    def get_local_state(self) -> list:
        local_state = []
        for k, v in self.app_spec.schema["local"]["declared"].items():
            local_state.append(pc.heading(getattr(self.AppState, k), font_size="2em"))
        return local_state

    def dapp_flow(self):
        return f"https://app.dappflow.org/explorer/application/{self.app_client.app_id}/transactions"
