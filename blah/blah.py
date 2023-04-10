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
                *pcap.render_actions(),
                *pcap.render_global_state(),
            ),
            bg="lightgreen",
            border_radius="15px",
            border_width="thin",
            padding=5,
        ),
        pc.box(element="iframe", src=pcap.dapp_flow(), width="100%", height="800px"),
    )


app = pc.App(state=pcap.AppState)
app.add_page(index)
app.compile()
