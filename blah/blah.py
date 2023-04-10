import pathlib
import pynecone as pc
from .pc_app import PCApp  # type: ignore

# relative to root where `pc run` is called
counter_path = "blah/application/artifacts/application.json"

specs = pathlib.Path("blah/specs")
amm_path = specs / "amm.json"
calculator_path = specs / "calculator.json"


pcap = PCApp.from_app_spec(str(calculator_path))


def index():
    return pc.vstack(
        pc.box(
            pc.vstack(
                *pcap.get_actions(),
                *pcap.get_global_state(),
            ),
            bg="lightgreen",
            border_radius="15px",
            border_color="green",
            border_width="thick",
            padding=5,
        ),
        pc.box(element="iframe", src=pcap.dapp_flow(), width="100%", height="800px"),
    )


app = pc.App(state=pcap.AppState)
app.add_page(index)
app.compile()


# class AppState(pc.State):
#    pass
#
# class Subber(AppState):
#    x: int = 0
#
#    def incr(self):
#        print(self)
#        print(dir(self))
#        print(self.__dict__)
#        self.x = self.x + 1
#
# def index():
#    return pc.badge(Subber.x, on_click=Subber.incr)
#
# app = pc.App(state=AppState)
# app.add_page(index)
# app.compile()
