from pyformlang.rsa import RecursiveAutomaton
from pyformlang.cfg import CFG

import networkx as nx
from scipy.sparse import csr_matrix, kron, eye
from itertools import product

from project.task02 import graph_to_nfa
from project.task03 import FiniteAutomaton


def cfpq_with_tensor(
    rsm: RecursiveAutomaton | CFG,
    graph: nx.DiGraph,
    start_nodes: set[int] = None,
    final_nodes: set[int] = None,
) -> set[tuple[int, int]]:
    if isinstance(rsm, CFG):
        rsm = cfg_to_rsm(rsm)

    start_nodes = graph.nodes if start_nodes is None else start_nodes
    final_nodes = graph.nodes if final_nodes is None else final_nodes

    fa = FiniteAutomaton(graph_to_nfa(graph, start_nodes, final_nodes))
    matrix, state_map, n_graph, int_map = (
        fa.matrix,
        fa.state_map,
        len(fa.int_map),
        fa.int_map,
    )

    rsm_matrix, n_rsm, rsm_state, rsm_start, rsm_final = rsm_to_mat(rsm)

    idx_to_state = {i: state for i, state in enumerate(product(int_map, rsm_state))}

    old = 0
    n = n_rsm * n_graph
    while True:
        symbols = rsm_matrix.keys() & matrix.keys()
        m = csr_matrix((n, n), dtype=bool) + eye(n, dtype=bool)
        if len(symbols) != 0:
            for symbol in symbols:
                m += kron(matrix[symbol], rsm_matrix[symbol])

        maybe_new = True
        maybe_old = m.nnz
        while maybe_new:
            m += m @ m
            maybe_new = maybe_old != m.nnz
            maybe_old = m.nnz

        if maybe_old == old:
            break
        old = maybe_old

        for from_idx, to_idx in zip(*m.nonzero()):
            from_graph_state, from_rsm_state = idx_to_state[from_idx]
            to_graph_state, to_rsm_state = idx_to_state[to_idx]
            if from_rsm_state in rsm_start and to_rsm_state in rsm_final:
                sym = from_rsm_state[0]
                from_graph_idx = state_map[from_graph_state]
                to_graph_idx = state_map[to_graph_state]
                matrix.setdefault(sym, csr_matrix((n_graph, n_graph), dtype=bool))[
                    from_graph_idx, to_graph_idx
                ] = True

    res = set()
    start = rsm.initial_label.value
    if start not in matrix:
        return res

    for from_graph_state, to_graph_state in product(start_nodes, final_nodes):
        from_graph_idx = state_map[from_graph_state]
        to_graph_idx = state_map[to_graph_state]
        if matrix[start][from_graph_idx, to_graph_idx]:
            res.add((from_graph_state, to_graph_state))
    return res


def cfg_to_rsm(cfg: CFG) -> RecursiveAutomaton:
    return RecursiveAutomaton.from_text(cfg.to_text())


def ebnf_to_rsm(ebnf: str) -> RecursiveAutomaton:
    return RecursiveAutomaton.from_text(ebnf)


def rsm_to_mat(
    rsm: RecursiveAutomaton,
) -> tuple[dict[str, csr_matrix], int, set, set, set]:
    n = sum([len(box.dfa.states) for box in rsm.boxes.values()])

    rsm_state = set()
    rsm_start = set()
    rsm_final = set()
    for sym, box in rsm.boxes.items():
        rsm_state |= {(sym.value, state.value) for state in box.dfa.states}
        rsm_start |= {(sym.value, state.value) for state in box.dfa.start_states}
        rsm_final |= {(sym.value, state.value) for state in box.dfa.final_states}

    rsm_matrix = {}
    state_map = {state: i for i, state in enumerate(rsm_state)}
    for sym, box in rsm.boxes.items():
        for from_state, transitions in box.dfa.to_dict().items():
            for symbol, to_state in transitions.items():
                from_idx = state_map[(sym.value, from_state.value)]
                to_idx = state_map[(sym.value, to_state.value)]
                rsm_matrix.setdefault(symbol.value, csr_matrix((n, n), dtype=bool))[
                    from_idx, to_idx
                ] = True

    return rsm_matrix, n, rsm_state, rsm_start, rsm_final
