"""Local full-state snapshots, including the simulator's nested objective closures."""

import importlib
import io
import marshal
import pickle
import types

from src.routing.road.NetworkBasic import NetworkBasic, Node, Edge
from src.routing.road.NetworkBasicWithStore import NetworkBasicWithStore


def _network(cls, state, node_rows, edge_rows, index, name):
    import pandas as pd
    network = cls.__new__(cls)
    nodes = {}
    for number, attributes, outgoing, incoming, previous, following in node_rows:
        node = Node.__new__(Node)
        node.__dict__.update(attributes)
        nodes[number] = node
    edges = {}
    for origin, destination, attributes in edge_rows:
        edge = Edge.__new__(Edge)
        edge.__dict__.update(attributes)
        edge.edge_index = (nodes[origin], nodes[destination])
        edges[origin, destination] = edge
    for number, attributes, outgoing, incoming, previous, following in node_rows:
        node = nodes[number]
        node.edges_to = {nodes[other]: edges[number, other] for other in outgoing}
        node.edges_from = {nodes[other]: edges[other, number] for other in incoming}
        node.prev = nodes[previous] if previous is not None else None
        node.next = nodes[following] if following is not None else None
    ordered = list(nodes.values())
    network.__dict__.update(state)
    network.nodes = pd.Series(ordered, index=index, name=name, dtype=object) if index is not None else ordered
    return network


def _cell(value):
    return (lambda: value).__closure__[0]


def _function(code, namespace, defaults, cells, attributes, name, qualname, module, kwdefaults, annotations):
    namespace = {"__builtins__": __builtins__, "__name__": module, **namespace}
    closure = tuple(_cell(value) for value in cells) if cells else None
    function = types.FunctionType(marshal.loads(code), namespace, name, defaults, closure)
    function.__qualname__ = qualname
    function.__module__ = module
    function.__kwdefaults__ = kwdefaults
    function.__annotations__ = annotations
    function.__dict__.update(attributes)
    return function


def _names(code):
    names = set(code.co_names)
    for value in code.co_consts:
        if isinstance(value, types.CodeType):
            names.update(_names(value))
    return names


class StatePickler(pickle.Pickler):
    def reducer_override(self, value):
        if type(value) in (NetworkBasic, NetworkBasicWithStore):
            # Flatten cyclic node/edge links while retaining both adjacency orders,
            # Dijkstra markers, live travel times, and routing caches exactly.
            nodes, edges = [], []
            for node in value.nodes:
                attributes = {key: item for key, item in node.__dict__.items()
                              if key not in ("edges_to", "edges_from", "prev", "next")}
                nodes.append((node.node_index, attributes,
                              [other.node_index for other in node.edges_to],
                              [other.node_index for other in node.edges_from],
                              node.prev.node_index if node.prev is not None else None,
                              node.next.node_index if node.next is not None else None))
                edges.extend((node.node_index, other.node_index,
                              {key: item for key, item in edge.__dict__.items() if key != "edge_index"})
                             for other, edge in node.edges_to.items())
            state = {key: item for key, item in value.__dict__.items() if key != "nodes"}
            index = getattr(value.nodes, "index", None)
            return _network, (type(value), state, nodes, edges,
                              None if callable(index) else index, getattr(value.nodes, "name", None))
        if isinstance(value, types.ModuleType):
            return importlib.import_module, (value.__name__,)
        if isinstance(value, types.FunctionType):
            if "<locals>" not in value.__qualname__ and value.__name__ != "<lambda>":
                try:
                    original = importlib.import_module(value.__module__)
                    for part in value.__qualname__.split("."):
                        original = getattr(original, part)
                    if original is value:
                        return NotImplemented
                except (ImportError, AttributeError):
                    pass
            namespace = {name: value.__globals__[name] for name in sorted(_names(value.__code__))
                         if name in value.__globals__ and name != "__builtins__"}
            return _function, (marshal.dumps(value.__code__), namespace, value.__defaults__,
                               tuple(cell.cell_contents for cell in (value.__closure__ or ())),
                               value.__dict__, value.__name__, value.__qualname__, value.__module__,
                               value.__kwdefaults__, value.__annotations__)
        return NotImplemented


def dumps(value):
    stream = io.BytesIO()
    StatePickler(stream, protocol=pickle.HIGHEST_PROTOCOL).dump(value)
    return stream.getvalue()


def loads(payload):
    return pickle.loads(payload)
