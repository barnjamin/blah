Experiment with Python frontend using [pynecone](https://pynecone.io/)

# Run it

Install [algokit](https://github.com/algorandfoundation/algokit-cli/) and spin up a local network with:

```bash
algokit localnet start
```

Run this honker

```bash
git clone git@github.com:barnjamin/blah.git
cd blah
python -m venv .venv
source .venv/bin/activate
(.venv) pip install -r requirements.txt
(.venv) pc run
```

Open http://localhost:3000 and click buttons

Click the `DappFlow` link to see the app in dappflow and find that the global state value matches 

# TODO

- [ ] Autogenerate the `State` class from the app spec
- [ ] Add wallet support
- [ ] Make it pretty
