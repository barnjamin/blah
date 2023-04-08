import beaker
import pyteal as pt


class State:
    count = beaker.GlobalStateValue(pt.TealType.uint64)


app = beaker.Application("pynecone-lol", state=State())


@app.create
def create() -> pt.Expr:
    return app.initialize_global_state()


@app.external
def increment() -> pt.Expr:
    return app.state.count.increment()


@app.external
def decrement() -> pt.Expr:
    return app.state.count.decrement()
