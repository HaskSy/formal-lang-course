from pyformlang.cfg import Terminal
from scipy.sparse import csr_matrix
from copy import deepcopy

from project.task06 import cfg_to_weak_normal_form


def cfpq_with_matrix(
    cfg,
    graph,
    start_nodes: set[int] = None,
    final_nodes: set[int] = None,
) -> set[tuple[int, int]]:
    start_nodes = graph.nodes if start_nodes is None else start_nodes
    final_nodes = graph.nodes if final_nodes is None else final_nodes

    cfg = cfg_to_weak_normal_form(cfg)
    n = len(graph.nodes)
    products = {p.head.value: csr_matrix((n, n), dtype=bool) for p in cfg.productions}
    accumulate = deepcopy(products)

    P_epsilon = set()
    P_terminal = {}
    P_mult = {}

    for p in cfg.productions:
        if len(p.body) == 0:
            P_epsilon.add(p.head.value)
        elif len(p.body) == 1 and isinstance(p.body[0], Terminal):
            P_terminal.setdefault(p.body[0].value, set()).add(p.head.value)
        elif len(p.body) == 2:
            P_mult.setdefault(p.head.value, set()).add(
                (p.body[0].value, p.body[1].value)
            )

    for n, m, tag in graph.edges.data("label"):
        if tag in P_terminal:
            for N in P_terminal[tag]:
                products[N][n, m] = True

    for N in P_epsilon:
        products[N].setdiag(True)

    new = True
    while new:
        new = False
        for N, mult in P_mult.items():
            prev = accumulate[N].nnz
            for L, R in mult:
                accumulate[N] += products[L] @ products[R]
            new |= prev != accumulate[N].nnz
        if new:
            for N, m in accumulate.items():
                products[N] += m

    start = cfg.start_symbol.value
    return {
        (n, m)
        for n, m in zip(*products[start].nonzero())
        if n in start_nodes and m in final_nodes
    }
