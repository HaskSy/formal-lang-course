from networkx import MultiDiGraph

from project.task11.notgraphql.notgraphqlVisitor import notgraphqlVisitor

from project.task12.type_checker import TypeContext, Type
from project.task02 import regex_to_dfa
from project.task03 import FiniteAutomaton, intersect_automata
from project.task07 import cfpq_with_matrix
from project.task08 import rsm_to_mat, cfpq_with_tensor

from pyformlang.rsa import RecursiveAutomaton
from pyformlang.finite_automaton import Symbol
from pyformlang.regular_expression import Regex
from copy import deepcopy

Int = int
IntPair = tuple[Int, Int]
Char = str
Graph = MultiDiGraph
Edge = tuple[Int, Int, Char]
SetInt = set[Int]
SetIntPair = set[IntPair]
Range = tuple[Int] | tuple[Int, Int | None]
FA = FiniteAutomaton
RSM = RecursiveAutomaton

AnyType = Int | IntPair | Char | Graph | Edge | SetInt | SetIntPair | Range | FA | RSM


def type_assertion(t: Type, o: AnyType) -> bool:
    match t:
        case Type.INT:
            return isinstance(o, Int)
        case Type.INT_PAIR:
            return (
                    isinstance(o, tuple) and
                    len(o) == 2 and
                    all(isinstance(item, int) for item in o)
            )
        case Type.CHAR:
            return isinstance(o, Char)
        case Type.FA:
            return isinstance(o, FA)
        case Type.RSM:
            return isinstance(o, RSM)
        case Type.SET_INT:
            return (
                    isinstance(o, set) and
                    all(isinstance(item, Int) for item in o)
            )
        case Type.SET_INT_PAIR:
            return (
                    isinstance(o, set) and
                    all(
                        isinstance(o, tuple) and
                        len(o) == 2 and
                        all(isinstance(i, Int) for i in item) for item in o
                    )
            )
        case Type.EDGE:
            return (isinstance(o, tuple) and
                    len(o) == 3 and
                    isinstance(o[0], Int) and
                    isinstance(o[1], Int) and
                    isinstance(o[2], Char)
                    )
        case Type.GRAPH:
            return isinstance(o, MultiDiGraph)
        case Type.RANGE:
            return isinstance(o, tuple) and \
            (len(o) == 1 and isinstance(o[0], Int)) and \
            (len(o) == 2 and isinstance(o[0], Int) and isinstance(o[1], Int | None))
        case _:
           return False


def make_fa(o: Char) -> FA:
    return FA(regex_to_dfa(o))


def rsm_repeat(a: FA | RSM, b: Range) -> FA | RSM:
    isFA: bool = isinstance(a, FA)
    fa1: Regex = FA(rsm_to_mat(a)[0]).to_regex() if isinstance(a, RSM) else a
    step: Regex = deepcopy(fa1)

    for _ in range(0, b[0] - 1):
        fa1 = fa1.union(step)
    result: Regex = Regex("") if b[0] == 0 else fa1

    if len(b) == 2:
        if b[1] is None:
            result = result.union(step.kleene_star())
        else:
            for _ in range(b[0], b[1]):
                fa1 = fa1.union(step)
                result = result.union(fa1)

    rec: RSM = RecursiveAutomaton.from_regex(result, Symbol("S"))
    return FA(rsm_to_mat(rec)[0]) if isFA else rec



def rsm_union(
        a: FA | RSM, b: FA | RSM
) -> FA | RSM:
    isFA: bool = isinstance(a, FA) and isinstance(b, FA)
    fa1: Regex = FA(rsm_to_mat(a)[0]).to_regex() if isinstance(a, RSM) else a
    fa2: Regex = FA(rsm_to_mat(b)[0]).to_regex() if isinstance(b, RSM) else b
    rec: RSM = RecursiveAutomaton.from_regex(fa1.union(fa2), Symbol("S"))
    return FA(rsm_to_mat(rec)[0]) if isFA else rec


def rsm_concat(
    a: FA | RSM, b: FA | RSM
) -> FA | RSM:
    isFA: bool = isinstance(a, FA) and isinstance(b, FA)
    fa1: Regex = FA(rsm_to_mat(a)[0]).to_regex() if isinstance(a, RSM) else a
    fa2: Regex = FA(rsm_to_mat(b)[0]).to_regex() if isinstance(b, RSM) else b
    rec: RSM = RecursiveAutomaton.from_regex(fa1.concatenate(fa2), Symbol("S"))
    return FA(rsm_to_mat(rec)[0]) if isFA else rec


def rsm_intersect(a: FA | RSM, b: FA | RSM) -> RSM:
    fa1: FA = FA(rsm_to_mat(a)[0]) if isinstance(a, RSM) else a
    fa2: FA = FA(rsm_to_mat(b)[0]) if isinstance(b, RSM) else b
    intersection = intersect_automata(fa1, fa2)
    return RecursiveAutomaton.from_regex(intersection.to_regex(), Symbol("S"))


class Context:
    def __init__(self):
        self.bindings = {}

    def bind(self, var: str, t: AnyType):
        self.bindings[var] = t

    def lookup(self, var):
        # После type-checking это должно быть гарантией, если это не так, ошибка в тайп чекере
        assert var in self.bindings, f"Variable '{var}' is not defined"
        if var in self.bindings:
            return self.bindings[var]


class InterpreterVisitor(notgraphqlVisitor):
    def __init__(self, tc: TypeContext):
        self.tc: TypeContext = tc
        self.context: Context = Context()

    def __get_subset(self):
        return dict(
            filter(
                lambda k: self.tc[k[0]] == Type.SET_INT_PAIR or self.tc[k[0]] == Type.SET_INT,
            self.context.bindings.items()))

    def visitProg(self, ctx):
        for stmt in ctx.stmt():
            self.visit(stmt)
        return self.__get_subset()

    def visitDeclare(self, ctx):
        var = ctx.VAR().getText()
        self.context.bind(var, MultiDiGraph())
        return None

    def visitBind(self, ctx):
        var = ctx.VAR().getText()
        eval = self.visit(ctx.expr())
        self.context.bind(var, eval)
        return None

    def visitRemove(self, ctx):
        var = ctx.VAR().getText()
        graph: MultiDiGraph = self.context.lookup(var)
        match ctx.getChild(1).getText():
            case "vertices":
                res: SetInt = self.visit(ctx.expr())
                graph.add_nodes_from(res)
            case "vertex":
                res: Int = self.visit(ctx.expr())
                graph.remove_node(res)
            case "edge":
                res: Edge = self.visit(ctx.expr())
                graph.remove_edge(*res)
        return None

    def visitAdd(self, ctx):
        var = ctx.VAR().getText()
        graph: MultiDiGraph = self.context.lookup(var)

        match ctx.getChild(1).getText():
            case "vertex":
                res: Int = self.visit(ctx.expr())
                graph.add_node(res)
            case "edge":
                res: Edge = self.visit(ctx.expr())
                graph.add_edge(*res)
        return None

    def visitExpr(self, ctx):
        if ctx.NUM():
            return int(ctx.getText())
        elif ctx.CHAR():
            return ctx.getText()
        elif ctx.VAR():
            return self.context.lookup(ctx.VAR().getText())
        elif ctx.edge_expr():
            return self.visitEdge_expr(ctx.edge_expr())
        elif ctx.set_expr():
            return self.visitSet_expr(ctx.set_expr())
        elif ctx.regexp():
            return self.visitRegexp(ctx.regexp())
        elif ctx.select():
            return self.visitSelect(ctx.select())
        else:
            raise Exception("Unknown expression type")

    def visitSet_expr(self, ctx) -> SetInt:
        elem_types = {self.visit(expr) for expr in ctx.expr()}
        return elem_types

    def visitEdge_expr(self, ctx) -> Edge:
        return tuple(self.visit(expr) for expr in ctx.expr())

    def visitRegexp(self, ctx) -> FA | RSM:
        if ctx.getChildCount() == 1:
            if ctx.CHAR():
                return make_fa(ctx.CHAR().getText())
            elif ctx.VAR():
                var = self.context.lookup(ctx.VAR().getText())
                assert type_assertion(self.tc.lookup(ctx.VAR().getText()), var)
                return var
        elif ctx.getChildCount() == 3 and ctx.range_():
            op = ctx.getChild(1).getText()
            left: FA | RSM = self.visit(ctx.regexp(0))
            right: Range = self.visit(ctx.range_())
            if op == "^":
                return rsm_repeat(left, right)
        elif ctx.getChildCount() == 3 and ctx.regexp(1):
            op = ctx.getChild(1).getText()
            left: FA | RSM = self.visit(ctx.regexp(0))
            right: FA | RSM = self.visit(ctx.regexp(1))
            if op == "|":
                return rsm_union(left, right)
            elif op == ".":
                return rsm_concat(left, right)
            elif op == "&":
                return rsm_intersect(left, right)
        elif ctx.getChildCount() == 3 and ctx.regexp(0):
            return self.visit(ctx.regexp(0))
        raise Exception("Unknown regular expression type")

    def visitRange(self, ctx) -> Range:
        n1: Int = self.visit(ctx.NUM(0))
        if ctx.getChild(2) != '..':
            return tuple(n1)
        n2: Int = self.visit(ctx.NUM(1)) if ctx.NUM(1) else None
        if n2 is not None and n2 < n1:
            raise Exception(f"Invalid range {n1}..{n2}")
        return n1, n2

    def visitSelect(self, ctx):
        def var_to_text(var):
            return var.symbol.text

        vf1 = ctx.v_filter(0) if ctx.v_filter(0) else None
        vf2 = ctx.v_filter(1) if ctx.v_filter(1) else None

        to_var = ctx.VAR()[-3]
        from_var = ctx.VAR()[-2]

        start_nodes: SetInt | None = None
        final_nodes: SetInt | None = None

        if vf1:
            var = var_to_text(vf1.VAR())
            if var == from_var:
                start_nodes = self.visit(vf1)
            elif var == to_var:
                final_nodes = self.visit(vf1)

        if vf2:
            var = var_to_text(vf2.VAR())
            if var == from_var:
                start_nodes = self.visit(vf2)
            elif var == to_var:
                final_nodes = self.visit(vf2)

        q: FA | RSM = self.visit(ctx.expr())
        g: Graph = self.visit(ctx.VAR()[-1])

        args = (q, g, start_nodes, final_nodes)
        res: SetIntPair = cfpq_with_tensor(*args) if isinstance(q, RSM) else cfpq_with_matrix(*args)
        match len(ctx.VAR()):
            case 5:
                return res
            case 4:
                var = var_to_text(ctx.VAR(0))
                if var == from_var:
                    return set(map(lambda x: x[0], res))
                elif var == to_var:
                    return set(map(lambda x: x[1], res))

    def visitV_filter(self, ctx) -> SetInt:
        return self.visit(ctx.expr())
