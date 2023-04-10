import pathlib
import pynecone as pc
from pc_app import PCApp  # type: ignore
from codegen import PyneconeStateCodeGen

# relative to root where `pc run` is called
counter_path = "blah/application/artifacts/application.json"

specs = pathlib.Path("blah/specs")
amm_path = specs / "amm.json"
calculator_path = specs / "calculator.json"


# pcap = PCApp.from_app_spec(str(calculator_path))
# def index():
#    return pc.vstack(
#        pc.box(
#            pc.vstack(
#                *pcap.get_actions(),
#                *pcap.get_global_state(),
#            ),
#            bg="lightgreen",
#            border_radius="15px",
#            border_color="green",
#            border_width="thick",
#            padding=5,
#        ),
#        pc.box(element="iframe", src=pcap.dapp_flow(), width="100%", height="800px"),
#    )
#
# app = pc.App(state=pcap.AppState)
# app.add_page(index)
# app.compile()


pcsg = PyneconeStateCodeGen.from_app_spec_path(str(calculator_path))
print(pcsg.src())


class State(pc.State):
    pass


class Wait(State):
    color: str = "red"

    def wat(self):
        self.color = "blue"


#
# def index():
#     return pc.badge(
#         "wat",
#         color=Wait.color,
#         bg="yellow",
#         border_color="black",
#         border_width="thick",
#         border_radius="1em",
#         on_mouse_over=Wait.wat,
#     )
# app = pc.App(state=State)
# app.add_page(index)
# app.compile()
#
#

