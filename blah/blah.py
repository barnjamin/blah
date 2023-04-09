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
        *pcap.get_actions(),
        *pcap.get_global_state(),
        pc.link("DappFlow", href=pcap.dapp_flow(), is_external=True),
    )


app = pc.App(state=pcap.AppState)
app.add_page(index)
app.compile()
