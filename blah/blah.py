import pathlib
import pynecone as pc
from .pc_app import PCApp  # type: ignore

# relative to root where `pc run` is called
# counter_path = "blah/application/artifacts/application.json"
# pcap = PCApp.from_app_spec(str(counter_path))

specs = pathlib.Path("blah/specs")

amm_path = specs / "amm.json"
pcap = PCApp.from_app_spec(str(amm_path))

calculator_path = specs / "calculator.json"
pcap = PCApp.from_app_spec(str(calculator_path))


def index():
    return pc.vstack(
        pc.box(
            pc.vstack(
                pc.heading("Actions"),
                *pcap.render_actions(),
                pc.spacer(),
                pc.heading("Global State"),
                *pcap.render_global_state(),
                width="100%"
            ),
            border_radius="15px",
            border_width="thin",
            border_color="black",
            padding=5,
        ),
        pc.box(
            element="iframe", src=pcap.dapp_flow_url(), width="100%", height="800px"
        ),
    )


app = pc.App(state=pcap.AppState)
app.add_page(index)
app.compile()
