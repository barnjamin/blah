import ast
import pathlib
import beaker
import algokit_utils as au
import pynecone as pc


class PyneconeStateCodeGen:
    """Generate the State class hierarchy for the App"""

    def __init__(self, app_spec: au.ApplicationSpecification):
        # ast.unparse

        self.native_ast = ast.fix_missing_locations(
            ast.Module(
                body=[
                    ast.ClassDef(
                        bases=[
                            ast.Attribute(
                                attr="State",
                                ctx=ast.Load(),
                                value=ast.Name(id="pc", ctx=ast.Load()),
                            ),
                        ],
                        body=[ast.Pass()],
                        name="AppState",
                        decorator_list=[],
                        keywords=[],
                    ),
                    ast.ClassDef(
                        bases=[ast.Name(id="AppState", ctx=ast.Load())],
                        body=[
                            ast.AnnAssign(
                                annotation=ast.Name(id="str", ctx=ast.Load()),
                                simple=1,
                                target=ast.Name(id="color", ctx=ast.Store()),
                                value=ast.Constant(value="red", kind=None),
                            ),
                            ast.FunctionDef(
                                args=ast.arguments(
                                    args=[
                                        ast.arg(annotation=None, arg="self"),
                                    ],
                                    defaults=[],
                                    kw_defaults=[],
                                    kwarg=None,
                                    kwonlyargs=[],
                                    posonlyargs=[],
                                    vararg=None,
                                ),
                                body=[
                                    ast.Assign(
                                        targets=[
                                            ast.Attribute(
                                                attr="color",
                                                ctx=ast.Store(),
                                                value=ast.Name(
                                                    id="self", ctx=ast.Load()
                                                ),
                                            ),
                                        ],
                                        value=ast.Name(id="self", ctx=ast.Load()),
                                    )
                                ],
                                decorator_list=[],
                                name="wat",
                                returns=None,
                            ),
                        ],
                        decorator_list=[],
                        keywords=[],
                        name="Wait",
                    ),
                ],
                type_ignores=[],
            )
        )

    def src(self) -> str:
        return ast.unparse(self.native_ast)

    @classmethod
    def from_app_spec_path(cls, path: str) -> "PyneconeStateCodeGen":
        """Load the app spec and return an instance of the class"""

        with open(path) as f:
            app_spec = au.ApplicationSpecification.from_json(f.read())

        return cls(app_spec)


# relative to root where `pc run` is called
counter_path = "blah/application/artifacts/application.json"

specs = pathlib.Path("blah/specs")
amm_path = specs / "amm.json"
calculator_path = specs / "calculator.json"

pcsg = PyneconeStateCodeGen.from_app_spec_path(str(calculator_path))
print(pcsg.src())
