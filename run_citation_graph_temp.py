import runpy
import sys

sys.path.insert(0, "C:/Users/tousi/Documents/ta_a5/Common/scigraph/src")
sys.argv = [
    "citation_graph",
    "--config",
    "C:/Users/tousi/Documents/ta_a5/Common/scigraph/configs/production.yaml",
]
runpy.run_module("scigraph.graph.citation_graph", run_name="__main__")
