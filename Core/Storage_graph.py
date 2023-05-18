import cython
import h5py
import traceback
import numpy as np
from aenum import IntEnum, extend_enum

from itertools import cycle, chain

from typing import *

from dataclasses import dataclass

import json
from functools import partial

hstr = h5py.string_dtype

cast_types = (
    (lambda v: isinstance(v, np.ndarray), lambda l: l.tolist()),
    (lambda v: np.issubdtype(v, np.bool_), bool),
    (lambda v: np.issubdtype(v, np.uint), int),
    (lambda v: np.issubdtype(v, int), int),
)
def cast(obj):
    for check_fn, cast_fn in cast_types:
        if(check_fn(obj)):
            return cast_fn(obj)
    return obj

def dumps(obj):
    return np.array(
        list(
            map(partial(json.dumps, default=cast), obj.flatten())
        ), dtype=np.string_
    ).reshape(obj.shape)

# All numpy arrays are treated as C++ vectors
# and they are not filled with data.
# Instead, we pre-allocate more data than
# we need now
@dataclass
class EdgeSet:
    kind: cython.uint
    source: cython.uint
    target: cython.uint
    edges: np.ndarray
    information: np.ndarray

    # variables for Fibbonacci and length
    _1: cython.uint
    _l: cython.uint

    # Per data
    _i2: cython.uint
    _il2: np.ndarray

@dataclass
class NodeSet:
    kind: cython.uint
    information: np.ndarray

    # variables for Fibbonacci and length
    # Per node
    _i1: cython.uint
    _il1: cython.uint

    # Per data
    _i2: cython.uint
    _il2: np.ndarray

class Graph:
    nodes: IntEnum
    edges: IntEnum

    _n: np.ndarray
    _e: np.ndarray

    # variables for Fibbonacci and length
    _n1: cython.uint
    _nl: cython.uint

    # variables for Fibbonacci and length
    _e1: cython.uint
    _el: cython.uint

    context: np.ndarray

    def __init__(self, expected_node_count: cython.uint=3, expected_edge_count: cython.uint=6, *, context: np.ndarray=None): 
        class NodeEnum(IntEnum):
            ...
        class EdgeEnum(IntEnum):
            ...
        
        self.nodes = NodeEnum
        self.edges = EdgeEnum

        self._nl = 0
        self._el = 0

        n0 = 8
        n1 = 5
        while n0 <= expected_node_count:
            n0, n1 = n0+n1, n0

        self._n1 = n1

        self._n = np.zeros(n0, dtype=object)

        while n0 <= expected_edge_count:
            n0, n1 = n0+n1, n0

        self._e1 = n1

        self._e = np.zeros(n0, dtype=object)

        self.context = context or np.zeros(0, dtype=object)

    def add_new_node_set(self, name: str):
        n0 = len(self._n)
        if(self._nl == n0):
            n0, self._n1 = n0 + self._n1, n0
            self._n.resize(n0, refcheck=False)
            print(f"Resized node sets to {n0}")

        info = np.zeros((8, 0, 2), dtype=object)
        il = np.zeros(0, dtype=np.uint16)
        
        kind = len(self.nodes)
        self._n[self._nl] = NodeSet(
            kind=kind,
            information=info,
            _i1=5,
            _il1=0,
            _i2=5,
            _il2=il,
        )
        self._nl += 1

        extend_enum(self.nodes, name, kind)
        print(f"Added node set \"{name}\": {kind}")
        return kind

    def add_new_edge_set(self, name: str, source: cython.uint, target: cython.uint):
        e0 = len(self._e)
        if(self._el == e0):
            e0, self._e1 = e0 + self._e1, e0
            self._e.resize(e0, refcheck=False)
            print(f"Resized edge sets to {e0}")

        edges = np.zeros((8, 9), dtype=np.uint16)
        info = np.zeros((8, 0, 2), dtype=object)
        il = np.zeros(0, dtype=np.uint16)

        kind = len(self.edges)
        self._e[self._el] = EdgeSet(
            kind=kind,
            source=source,
            target=target,
            edges=edges,
            information=info,
            _1=5,
            _l=0,
            _i2=5,
            _il2=il,
        )

        self._el += 1

        extend_enum(self.edges, name, kind)
        print(f"Added edge set \"{name}\": {kind}")
        return kind
        
    def add_node(self, node_kind: cython.uint) -> cython.uint:
        nodeset: NodeSet = self._n[node_kind]
        index = nodeset._il1
        nodeset._il1 += 1

        print(f"Added node {index} of {node_kind}")
        return index

    def add_nodes(self, node_kind: cython.uint, num_nodes: cython.uint) -> cython.uint:
        nodeset: NodeSet = self._n[node_kind]
        index = nodeset._il1
        nodeset._il1 += num_nodes

        print(f"Added {num_nodes} nodes of {node_kind}")
        return index, nodeset._il1

    def connect_nodes(self, 
                      edge_kind: cython.uint, 
                      node_s_i: cython.uint,
                      node_t_i: cython.uint,
                      ) -> cython.uint:
        src_edgeset: EdgeSet = self._e[edge_kind]

        # nodeset.edges[node_k, node_i, 2]!!
        r0 = None
        e0 = len(src_edgeset.edges)
        if(node_s_i >= e0):
            e0, src_edgeset._1 = e0 + src_edgeset._1, e0
            while(node_s_i >= e0):
                e0, src_edgeset._1 = e0 + src_edgeset._1, e0
            r0 = e0

        if(r0 is not None):
            src_edgeset._il2.resize(r0, refcheck=False)

        r2 = None
        l2 = src_edgeset.edges.shape[1]
        l = src_edgeset._il2[node_s_i] + 1
        if(l > l2 and (r2 is None or l > r2)):
            r2 = l

        if(r0 is not None or r2 is not None):
            src_edgeset.edges.resize((
                r0 or e0,
                r2 or l2
            ), refcheck=False)
            print(f"Resized edges to {(r0 or e0,r2 or l2)}")

        src_edgeset.edges[node_s_i, src_edgeset._il2[node_s_i]] = node_t_i
        src_edgeset._il2[node_s_i] += 1

        self._e[edge_kind]._l += 1

        print(f"Added connection of {edge_kind}: {node_s_i} -> {node_t_i}")

    def connect_many_nodes(self,
                      edge_kind: cython.uint, 
                      node_s_i: list,
                      node_t_i: list,
                      ) -> None:
        assert len(node_s_i) == len(node_t_i)
        src_edgeset: EdgeSet = self._e[edge_kind]

        # nodeset.edges[node_k, node_i, 2]!!
        r0 = None
        e0 = len(src_edgeset._il2)
        max_s_i = max(node_s_i)
        if(max_s_i >= e0):
            e0, src_edgeset._1 = e0 + src_edgeset._1, e0
            while(max_s_i >= e0):
                e0, src_edgeset._1 = e0 + src_edgeset._1, e0
            r0 = e0

        if(r0 is not None):
            src_edgeset._il2.resize(r0, refcheck=False)

        new_il2 = np.copy(src_edgeset._il2)

        r2 = None
        l2 = src_edgeset.edges.shape[1]
        for s_i in node_s_i:
            l = new_il2[s_i] = new_il2[s_i] + 1
            
            if(l > l2 and (r2 is None or l > r2)):
                r2 = l

        if(r0 is not None or r2 is not None):
            src_edgeset.edges.resize((
                r0 or e0,
                r2 or l2
            ), refcheck=False)
            print(f"Resized edges to {(r0 or e0,r2 or l2)}")

        for s_i, t_i in zip(node_s_i, node_t_i):
            src_edgeset.edges[s_i, src_edgeset._il2[s_i]] = t_i
            src_edgeset._il2[s_i] += 1

        self._e[edge_kind]._l += len(node_s_i)

        print(f"Added {len(node_s_i)} connections of {edge_kind}")
    
    def set_node_information(self, node_kind, node_i, key, value, index=None) -> None:
        nodeset: NodeSet = self._n[node_kind]

        r0 = None
        i0 = len(nodeset.information)
        if(node_i >= i0):
            while(node_i >= i0):
                i0, nodeset._i1 = i0 + nodeset._i1, i0
            r0 = i0

        if(r0 is not None):
            nodeset._il2.resize(r0, refcheck=False)

        r2 = None
        l2 = nodeset.information.shape[1]
        l = nodeset._il2[node_i] + 1
        
        if(l > l2 and (r2 is None or l > r2)):
            r2 = l

        if(r0 is not None or r2 is not None):
            nodeset.information.resize((
                    r0 or i0,
                    r2 or l2,
                    2
                ),
                refcheck=False
            )
            print(f"Resized nodeset {node_kind} information to {(r0 or i0, r2 or l2, 2)}")

        nodeset.information[node_i, nodeset._il2[node_i]] = (key, value)
        nodeset._il2[node_i] += 1
        print(f"Set information for node {node_i} ({key}: {value})")

    def set_nodes_information(self, node_kind, nodes_i, keys, values, index=None) -> None:
        nodeset: NodeSet = self._n[node_kind]

        node_i = max(nodes_i)
        r0 = None
        i0 = len(nodeset._il2)
        if(node_i >= i0):
            i0, nodeset._i1 = i0 + nodeset._i1, i0
            while(node_i >= i0):
                i0, nodeset._i1 = i0 + nodeset._i1, i0
            r0 = i0

        if(r0 is not None):
            nodeset._il2.resize(r0, refcheck=False)

        
        new_il2 = np.copy(nodeset._il2)

        r2 = None
        l2 = nodeset.information.shape[1]
        for n_i, num_values in zip(nodes_i, map(len, values)):
            l = new_il2[n_i] = new_il2[n_i] + num_values
            
            if(l > l2 and (r2 is None or l > r2)):
                r2 = l

        if(r0 is not None or r2 is not None):
            nodeset.information.resize((
                    r0 or i0,
                    r2 or l2,
                    2
                ),
                refcheck=False
            )
            print(f"Resized nodeset {node_kind} information to {(r0 or i0, r2 or l2, 2)}")

        for node_i, node_keys, node_values in zip(nodes_i, keys, values):
            for key, value in zip(node_keys, node_values):
                nodeset.information[node_i, nodeset._il2[node_i]] = (key, value)
                nodeset._il2[node_i] += 1
        print(f"Set information for {len(nodes_i)} nodes")

    def set_edge_information(self, edge_kind, edge_i, key, value, index=None) -> None:
        edgeset: NodeSet = self._e[edge_kind]

        r0 = None
        i0 = len(edgeset.information)
        if(edge_i >= i0):
            while(edge_i >= i0):
                i0, edgeset._1 = i0 + edgeset._1, i0
            r0 = i0

        if(r0 is not None):
            edgeset._il2.resize(r0, refcheck=False)
        
        r2 = None
        l2 = edgeset.information.shape[1]
        l = edgeset._il2[edge_i] + 1
        
        if(l > l2 and (r2 is None or l > r2)):
            r2 = l

        if(r0 is not None or r2 is not None):
            edgeset.information.resize((
                    r0 or i0,
                    r2 or l2,
                    2
                ),
                refcheck=False
            )
            print(f"Resized edgeset {edge_kind} information to {(r0 or i0, r2 or l2, 2)}")

        edgeset.information[edge_i, edgeset._il2[edge_i]-1] = (key, value)
        edgeset._il2[edge_i] += 1
        print(f"Set information for edge {edge_i} ({key}: {value})")

    def set_edges_information(self, edge_kind, edges_i, keys, values, index=None) -> None:
        edgeset: NodeSet = self._e[edge_kind]

        edge_i = max(edges_i)
        r0 = None
        i0 = len(edgeset._il2)
        if(edge_i >= i0):
            i0, edgeset._1 = i0 + edgeset._1, i0
            while(edge_i >= i0):
                i0, edgeset._1 = i0 + edgeset._1, i0
            r0 = i0

        if(r0 is not None):
            edgeset._il2.resize(r0, refcheck=False)
        
        new_il2 = np.copy(edgeset._il2)

        r2 = None
        l2 = edgeset.information.shape[1]
        for e_i, num_values in zip(edges_i, map(len, values)):
            l = new_il2[e_i] = new_il2[e_i] + num_values
            
            if(l > l2 and (r2 is None or l > r2)):
                r2 = l

        if(r0 is not None or r2 is not None):
            edgeset.information.resize((
                    r0 or i0,
                    r2 or l2,
                    2
                ),
                refcheck=False
            )
            print(f"Resized edgeset {edge_kind} information to {(r0 or i0, r2 or l2, 2)}")

        for edge_i, edge_keys, edge_values in zip(edges_i, keys, values):
            for key, value in zip(edge_keys, edge_values):
                edgeset.information[edge_i, edgeset._il2[edge_i]-1] = (key, value)
                edgeset._il2[edge_i] += 1
        print(f"Set information for {len(edges_i)} edges")

    def get_node_information(self, node_kind, node_i):
        return self._n[node_kind].information[node_i]

    def get_edge_information(self, edge_kind, edge_i):
        return self._e[edge_kind].information[edge_i]
    
    def add_nodes_from_df(self, nodeset: str, dataframe: pd.DataFrame):
        nodeset_num: int
        if(type(nodeset) == int):
            nodeset_num = nodeset
        elif(hasattr(self.nodes, nodeset)):
            nodeset_num = self.nodes[nodeset].value
        else:
            nodeset_num = self.add_new_node_set(nodeset)

        new_nodes_range = self.add_nodes(nodeset_num, len(dataframe))
        self.set_nodes_information(
            nodeset_num,
            range(*new_nodes_range),
            cycle([dataframe.columns]),
            dataframe.iloc
        )

    def add_edges_from_df(self, 
            edgeset: str,
            src_nodeset: str,
            tar_nodeset: str,
            dataframe: pd.DataFrame,
            src_col: str = "source_id",
            tar_col: str = "target_id"):
        src_nodeset_num: int
        if(type(src_nodeset) == int):
            src_nodeset_num = src_nodeset
        elif(hasattr(self.nodes, src_nodeset)):
            src_nodeset_num = self.nodes[src_nodeset].value
        else:
            raise ValueError(f"Source nodeset \"{src_nodeset}\" does not exist")

        tar_nodeset_num: int
        if(type(tar_nodeset) == int):
            tar_nodeset_num = tar_nodeset
        elif(hasattr(self.nodes, tar_nodeset)):
            tar_nodeset_num = self.nodes[tar_nodeset].value
        else:
            raise ValueError(f"Target nodeset \"{tar_nodeset}\" does not exist")

        edgeset_num: int
        if(type(edgeset) == int):
            edgeset_num = edgeset
        elif(hasattr(self.edges, edgeset)):
            edgeset_num = self.edges[edgeset].value
        else:
            edgeset_num = self.add_new_edge_set(edgeset, src_nodeset_num, tar_nodeset_num)

        self.connect_many_nodes(
            edgeset_num, 
            dataframe[src_col],
            dataframe[tar_col],
        )
        self.set_edges_information(
            edgeset_num,
            dataframe[src_col],
            cycle([dataframe.columns]),
            dataframe.iloc
        )

    def to_df(self):
        nodes = {}
        for node_enum in self.nodes:
            nodeset = self._n[node_enum.value]
            nodes[node_enum.name] = pd.DataFrame([
                {k:v for k,v in info if k != 0}
                for ni, info in enumerate(nodeset.information[:nodeset._il1])
                if nodeset._il2[ni] != 0
            ])

        edges = {}
        for edge_enum in self.edges:
            edgeset = self._e[edge_enum.value]
            edges[edge_enum.name] = pd.DataFrame([
                {k:v for k,v in info if k != 0}
                for ni, info in enumerate(edgeset.information[:edgeset._l])
                if edgeset._il2[ni] != 0
            ])

        return [nodes, edges, self.context]

    # TODO: Accummulative hdf5

    def to_hdf5(self, file: Union[str, h5py.File]):
        if(type(file) == str):
            file = h5py.File(file, 'w')
        elif(not isinstance(file, h5py.File)):
            raise ValueError("file must be either a string or a h5py.File")

        print(f"Storing into \"{file}\"")

        try:
          nodes_gr = file.create_group('Nodes')
          edges_gr = file.create_group('Edges')
          context = file.create_dataset("Context", self.context.shape, dtype=hstr())

          context[:] = dumps(self.context)

          nodes_gr.attrs['_n1'] = self._n1
          nodes_gr.attrs['_nl'] = self._nl

          edges_gr.attrs['_e1'] = self._e1
          edges_gr.attrs['_el'] = self._el

          for nodeset_enum in self.nodes:
            print(f" N Storing node {nodeset_enum.name}")
            node_gr = nodes_gr.create_group(nodeset_enum.name)
            nodeset: NodeSet = self._n[nodeset_enum.value]

            node_gr.attrs['kind'] = nodeset.kind
            node_gr.attrs['_i1'] = nodeset._i1
            node_gr.attrs['_il1'] = nodeset._il1
            node_gr.attrs['_i2'] = nodeset._i2
            node_gr.attrs['_il2'] = nodeset._il2

            info = node_gr.create_dataset("information", nodeset.information.shape, maxshape=(None,None,2), dtype=hstr())
            info[:] = dumps(nodeset.information)

          for edgeset_enum in self.edges:
            print(f" E Storing edge {edgeset_enum.name}")
            edge_gr = edges_gr.create_group(edgeset_enum.name)
            edgeset: EdgeSet = self._e[edgeset_enum.value]

            edge_gr.attrs['kind'] = edgeset.kind
            edge_gr.attrs['source'] = edgeset.source
            edge_gr.attrs['target'] = edgeset.target
            edge_gr.attrs['_1'] = edgeset._1
            edge_gr.attrs['_l'] = edgeset._l
            edge_gr.attrs['_i2'] = edgeset._i2
            edge_gr.attrs['_il2'] = edgeset._il2

            edges = edge_gr.create_dataset("edges", edgeset.edges.shape, maxshape=(None,None), dtype=np.int16)
            edges[:] = edgeset.edges

            info = edge_gr.create_dataset("information", edgeset.information.shape, maxshape=(None,None,2), dtype=hstr())
            info[:] = dumps(edgeset.information)

        except Exception:
          print(traceback.format_exc())
        finally:
          print("Closing file")
          file.close()

    @staticmethod
    def from_hdf5(file: Union[str, h5py.File]):
        if(type(file) == str):
            file = h5py.File(file, 'r')
        elif(not isinstance(file, h5py.File)):
            raise ValueError("file must be either a string or a h5py.File")

        print(f"Loading \"{file}\"")

        try:
            graph = Graph(
                expected_node_count=file['Nodes'].attrs['_nl'],
                expected_edge_count=file['Edges'].attrs['_el'],
                context=np.array(list(map(json.loads, file['Context'][:]))),
            )

            for nodeset_name, nodeset in sorted(file['Nodes'].items(), key=lambda n: n[1].attrs['kind']):
                nodeset_num = graph.add_new_node_set(nodeset_name)
                nodeset_obj = graph._n[nodeset_num]

                for attr, value in nodeset.attrs.items():
                    setattr(nodeset_obj, attr.lower(), value)
                
                for attr, value in nodeset.items():
                    if(value.dtype == object):
                        setattr(nodeset_obj, attr.lower(), np.array(list(map(json.loads, value[:].flatten()))).reshape(value.shape))
                    else:
                        setattr(nodeset_obj, attr.lower(), value[:])

            for edgeset_name, edgeset in sorted(file['Edges'].items(), key=lambda n: n[1].attrs['kind']):
                edgeset_num = graph.add_new_edge_set(edgeset_name, 0, 0)
                edgeset_obj = graph._e[edgeset_num]

                for attr, value in edgeset.attrs.items():
                    setattr(edgeset_obj, attr.lower(), value)
                
                for attr, value in edgeset.items():
                    if(value.dtype == object):
                        setattr(edgeset_obj, attr.lower(), np.array(list(map(json.loads, value[:].flatten()))).reshape(value.shape))
                    else:
                        setattr(edgeset_obj, attr.lower(), value[:])

        except Exception:
            print(traceback.format_exc())
        finally:
            print("Closing file")
            file.close()

        return graph
    
    def __repr__(self):
        return f"<Graph Nodes {[n.name for n in self.nodes]}, Edges {[e.name for e in self.edges]}>"