from copy import deepcopy
import networkx as nx
from pyformlang.cfg import CFG
from pyformlang.rsa import RecursiveAutomaton
from project.task08 import cfg_to_rsm


def cfpq_with_gll(
    rsm: RecursiveAutomaton,
    graph: nx.DiGraph,
    start_nodes: set[int] = None,
    final_nodes: set[int] = None,
) -> set[tuple[int, int]]:
    rsm = cfg_to_rsm(rsm) if isinstance(rsm, CFG) else rsm
    start_nodes = start_nodes if start_nodes is not None else set(graph.nodes)
    final_nodes = final_nodes if final_nodes is not None else set(graph.nodes)

    initial_label = (
        rsm.initial_label.value if rsm.initial_label.value is not None else "S"
    )

    start_states = {(initial_label, node) for node in start_nodes}
    state_graph = {state: set() for state in start_states}
    visited_states = {
        (
            state[1],
            (initial_label, rsm.boxes[rsm.initial_label].dfa.start_state.value),
            state,
        )
        for state in start_states
    }
    queue = deepcopy(visited_states)

    popped_states = {}
    result_pairs = set()

    while queue:
        graph_node, automaton_state, stack_state = queue.pop()

        if automaton_state[1] in rsm.boxes[automaton_state[0]].dfa.final_states:
            if stack_state in start_states and graph_node in final_nodes:
                result_pairs.add((stack_state[1], graph_node))
            popped_states.setdefault(stack_state, set()).add(graph_node)
            for previous_stack_state, previous_automaton_state in state_graph.get(
                stack_state, set()
            ):
                new_state = (graph_node, previous_automaton_state, previous_stack_state)
                if new_state not in visited_states:
                    queue.add(new_state)
                    visited_states.add(new_state)

        outgoing_edges = {}
        for _, neighbor, label in graph.edges(graph_node, data="label"):
            if label not in outgoing_edges:
                outgoing_edges[label] = set()
            outgoing_edges[label].add(neighbor)

        transitions = (
            rsm.boxes[automaton_state[0]].dfa.to_dict().get(automaton_state[1], {})
        )
        for symbol, to_state in transitions.items():
            if symbol not in rsm.labels:
                if symbol.value in outgoing_edges:
                    for next_node in outgoing_edges[symbol.value]:
                        new_state = (
                            next_node,
                            (automaton_state[0], to_state.value),
                            stack_state,
                        )
                        if new_state not in visited_states:
                            queue.add(new_state)
                            visited_states.add(new_state)
            else:
                new_stack_state = (symbol.value, graph_node)
                if new_stack_state in popped_states:
                    for next_node in popped_states[new_stack_state]:
                        new_state = (
                            next_node,
                            (automaton_state[0], to_state.value),
                            stack_state,
                        )
                        if new_state not in visited_states:
                            queue.add(new_state)
                            visited_states.add(new_state)

                state_graph.setdefault(new_stack_state, set()).add(
                    (stack_state, (automaton_state[0], to_state.value))
                )
                new_state = (
                    graph_node,
                    (symbol.value, rsm.boxes[symbol].dfa.start_state.value),
                    new_stack_state,
                )
                if new_state not in visited_states:
                    queue.add(new_state)
                    visited_states.add(new_state)

    return result_pairs
