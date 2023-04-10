import beaker
import application as app  # type: ignore


def main() -> None:
    accts = beaker.sandbox.get_accounts()
    algod = beaker.sandbox.get_algod_client()

    creator = accts.pop()
    app_client = beaker.client.ApplicationClient(algod, app.app, signer=creator.signer)
    app_client.create()

    app_client.call(app.increment)
    app_client.call(app.increment)
    app_client.call(app.decrement)

    gs = app_client.get_global_state()
    print(gs)


if __name__ == "__main__":
    app.app.build().export("./artifacts")
    main()
