from networkx import MultiDiGraph

from project.task11.notgraphql.notgraphqlVisitor import notgraphqlVisitor

from project.task12.type_checker import TypeContext, Type
from project.task03 import FiniteAutomaton
from project.task07 import cfpq_with_matrix
from project.task08 import rsm_to_mat, cfg_to_rsm
from project.task09 import cfpq_with_gll

from pyformlang.rsa import RecursiveAutomaton
from pyformlang.finite_automaton import Symbol
from pyformlang.regular_expression import Regex
from pyformlang.cfg import CFG, Variable, Terminal
from copy import deepcopy

Int = int
IntPair = tuple[Int, Int]
Char = str
Graph = MultiDiGraph
Edge = tuple[Int, Char, Int]
SetInt = set[Int]
SetIntPair = set[IntPair]
Range = tuple[Int] | tuple[Int, Int | None]
FA = CFG
RSM = RecursiveAutomaton
Regex = Regex

AnyType = (
    Int | IntPair | Char | Graph | Edge | SetInt | SetIntPair | Range | FA | RSM | Regex
)


def type_assertion(t: Type, o: AnyType) -> bool:
    match t:
        case Type.INT:
            return isinstance(o, Int)
        case Type.INT_PAIR:
            return (
                isinstance(o, tuple)
                and len(o) == 2
                and all(isinstance(item, int) for item in o)
            )
        case Type.CHAR:
            return isinstance(o, Char)
        case Type.FA:
            return isinstance(o, FA)
        case Type.RSM:
            return isinstance(o, RSM)
        case Type.SET_INT:
            return isinstance(o, set) and all(isinstance(item, Int) for item in o)
        case Type.SET_INT_PAIR:
            return isinstance(o, set) and all(
                isinstance(o, tuple)
                and len(o) == 2
                and all(isinstance(i, Int) for i in item)
                for item in o
            )
        case Type.EDGE:
            return (
                isinstance(o, tuple)
                and len(o) == 3
                and isinstance(o[0], Int)
                and isinstance(o[1], Int)
                and isinstance(o[2], Char)
            )
        case Type.GRAPH:
            return isinstance(o, MultiDiGraph)
        case Type.RANGE:
            return (
                isinstance(o, tuple)
                and (len(o) == 1 and isinstance(o[0], Int))
                and (
                    len(o) == 2
                    and isinstance(o[0], Int)
                    and isinstance(o[1], Int | None)
                )
            )
        case Type.REGEX:
            return isinstance(o, Regex)
        case _:
            return False


def cast(o: AnyType, t: Type) -> AnyType:
    if type_assertion(t, o):
        return o
    if type_assertion(Type.CHAR, o) and t == Type.FA:
        return Regex(o).to_cfg()
    if type_assertion(Type.CHAR, o) and t == Type.RSM:
        return RSM.from_regex(Regex(o), Symbol("S"))
    if type_assertion(Type.REGEX, o) and t == Type.FA:
        return o.to_cfg()
    if type_assertion(Type.REGEX, o) and t == Type.RSM:
        return RSM.from_regex(Regex(o), Symbol("S"))
    if type_assertion(Type.FA, o) and t == Type.RSM:
        return cfg_to_rsm(o)
    if type_assertion(Type.RSM, o) and t == Type.FA:
        return FiniteAutomaton(rsm_to_mat(o)[0]).to_regex().to_cfg()
    if type_assertion(Type.RSM, o) and t == Type.REGEX:
        return FiniteAutomaton(rsm_to_mat(o)[0]).to_regex()
    if type_assertion(Type.FA, o) and t == Type.REGEX:
        return FiniteAutomaton(rsm_to_mat(cfg_to_rsm(o))[0]).to_regex()
    raise Exception(f"Cast from {type(o)} to {t} is not defined")


def repeat(a: FA | RSM, b: Range) -> FA | RSM:
    return_type: Type = Type.FA if type_assertion(Type.FA, a) else Type.RSM
    fa1: FA = cast(a, Type.FA)
    step: FA = deepcopy(fa1)

    for _ in range(0, b[0] - 1):
        fa1 = fa1.concatenate(step)
    result: FA = cast(Regex("$"), Type.FA) if b[0] == 0 else fa1

    if len(b) == 2:
        if b[1] is None:
            result = result.union(cast(cast(step, Type.REGEX).kleene_star(), Type.FA))
        else:
            for _ in range(b[0], b[1]):
                fa1 = fa1.union(step)
                result = result.union(fa1)

    return cast(result, return_type)


def repeat_regex(a: str, b: Range) -> str:
    fa1: str = a
    step: str = deepcopy(fa1)

    for _ in range(0, b[0] - 1):
        fa1 = f"{fa1} {step}"
    result: str = "$" if b[0] == 0 else fa1

    if len(b) == 2:
        if b[1] is None:
            result = f"({result}) | ({step})*"
        else:
            result = f"({result})"
            for _ in range(b[0], b[1]):
                fa1 = f"{fa1} | {step}"
                result = f"{result} | ({fa1})"

    return result


def union(a: FA | RSM, b: FA | RSM) -> FA | RSM:
    return_type: Type = (
        Type.FA
        if type_assertion(Type.FA, a) and type_assertion(Type.FA, b)
        else Type.RSM
    )
    fa1: FA = cast(a, Type.FA)
    fa2: FA = cast(b, Type.FA)
    rec: FA = fa1.union(fa2)
    return cast(rec, return_type)


def concat(a: FA | RSM, b: FA | RSM) -> FA | RSM:
    return_type: Type = (
        Type.FA
        if type_assertion(Type.FA, a) and type_assertion(Type.FA, b)
        else Type.RSM
    )
    fa1: FA = cast(a, Type.FA)
    fa2: FA = cast(b, Type.FA)
    rec: FA = fa1.concatenate(fa2)
    return cast(rec, return_type)


def intersect(a: FA | RSM, b: FA | RSM) -> RSM:
    return_type: Type = (
        Type.FA
        if type_assertion(Type.FA, a) and type_assertion(Type.FA, b)
        else Type.RSM
    )
    fa1: FA = cast(a, Type.FA)
    fa2: FA = cast(b, Type.FA)
    rec: FA = fa1.intersection(fa2)
    return cast(rec, return_type)


class Context:
    def __init__(self, tc: TypeContext):
        self.tc = tc
        self.bindings = {}
        self.ebnf_map = {}

    def bind(self, var: str, t: AnyType) -> None:
        if self.tc.lookup(var) == Type.RSM:
            self.bindings[var] = cast(t, Type.RSM)
        if type_assertion(Type.CHAR, t):
            self.bindings[var] = cast(t, Type.FA)
        else:
            self.bindings[var] = t

    def lookup(self, var) -> AnyType:
        if var in self.bindings:
            return self.bindings[var]
        return cast(FA(variables={Variable(value=var)}), Type.RSM)

    def get_nonterm(self, var: str):
        return var.upper()

    def get_ebnf(self, var: str):
        return self.ebnf_map[var]

    def put_ebnf(self, var: str, fa: str):
        self.ebnf_map[var] = f"{var} -> {fa}"


class InterpreterVisitor(notgraphqlVisitor):
    def __init__(self, tc: TypeContext):
        self.tc: TypeContext = tc
        self.context: Context = Context(tc)

    def __get_subset(self):
        return dict(
            filter(
                lambda k: self.tc.lookup(k[0]) == Type.SET_INT_PAIR
                or self.tc.lookup(k[0]) == Type.SET_INT,
                self.context.bindings.items(),
            )
        )

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
        if self.tc.lookup(var) is Type.RSM:
            eval: str = self.visitRSMRegexp(ctx.expr())
            print(eval)
            self.context.put_ebnf(var, eval)
            self.context.bind(
                var, RecursiveAutomaton.from_regex(Regex(eval), Symbol(var))
            )
        else:
            eval = self.visitExpr(ctx.expr())
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
                u, label, v = res
                graph.add_edge(u, v, label=label)
        return None

    def visitExpr(self, ctx) -> AnyType:
        if ctx.NUM():
            return Int(ctx.getText())
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

    def visitRSMRegexp(self, ctx) -> str:
        if ctx.getChildCount() == 1:
            if ctx.CHAR():
                return ctx.CHAR().getText()
            elif ctx.VAR():
                return self.context.get_nonterm(ctx.VAR().getText())
            elif ctx.regexp():
                return self.visitRSMRegexp(ctx.regexp())
        elif ctx.getChildCount() == 3 and ctx.range_():
            op = ctx.getChild(1).getText()
            left_cfg: str = self.visitRSMRegexp(ctx.regexp(0))
            range_cfg = self.visitRange(ctx.range_())
            if op == "^":
                return repeat_regex(left_cfg, range_cfg)
        elif ctx.getChildCount() == 3 and ctx.regexp(1):
            op = ctx.getChild(1).getText()
            if op == "|":
                left_cfg: str = self.visitRSMRegexp(ctx.regexp(0))
                right_cfg: str = self.visitRSMRegexp(ctx.regexp(1))
                return f"({left_cfg}) | ({right_cfg})"
            elif op == ".":
                left_cfg: str = self.visitRSMRegexp(ctx.regexp(0))
                right_cfg: str = self.visitRSMRegexp(ctx.regexp(1))
                return f"{left_cfg}.{right_cfg}"
            elif op == "&":
                left_cfg: CFG = CFG.from_text(
                    self.context.get_ebnf(ctx.regexp(0).VAR().getText())
                )
                right_cfg: CFG = CFG.from_text(
                    self.context.get_ebnf(ctx.regexp(1).VAR().getText())
                )
                return left_cfg.intersection(right_cfg).to_text()
        elif ctx.getChildCount() == 3 and ctx.regexp(0):
            return self.visitRSMRegexp(ctx.regexp(0))
        raise Exception("Unknown regular expression type")

    def visitRegexp(self, ctx) -> FA | RSM:
        if ctx.getChildCount() == 1:
            if ctx.CHAR():
                return cast(ctx.CHAR().getText(), Type.FA)
            elif ctx.VAR():
                var = self.context.lookup(ctx.VAR().getText())
                assert type_assertion(
                    self.tc.lookup(ctx.VAR().getText()), var
                ), f"Expected type '{self.tc.lookup(ctx.VAR().getText())}' but got '{var}'"
                return var
        elif ctx.getChildCount() == 3 and ctx.range_():
            op = ctx.getChild(1).getText()
            left: FA | RSM = self.visit(ctx.regexp(0))
            right: Range = self.visit(ctx.range_())
            if op == "^":
                return repeat(left, right)
        elif ctx.getChildCount() == 3 and ctx.regexp(1):
            op = ctx.getChild(1).getText()
            left: FA | RSM = self.visit(ctx.regexp(0))
            right: FA | RSM = self.visit(ctx.regexp(1))
            if op == "|":
                return union(left, right)
            elif op == ".":
                return concat(left, right)
            elif op == "&":
                return intersect(left, right)
        elif ctx.getChildCount() == 3 and ctx.regexp(0):
            return self.visit(ctx.regexp(0))
        raise Exception("Unknown regular expression type")

    def visitRange(self, ctx) -> Range:
        n1: Int = Int(ctx.NUM(0).getText())
        if ctx.getChild(2).getText() != "..":
            return tuple(n1)
        n2: Int = Int(ctx.NUM(1).getText()) if ctx.NUM(1) else None
        if n2 is not None and n2 < n1:
            raise Exception(f"Invalid range {n1}..{n2}")
        return n1, n2

    def visitSelect(self, ctx):
        def var_to_text(var):
            return var.symbol.text

        vf1 = ctx.v_filter(0) if ctx.v_filter(0) else None
        vf2 = ctx.v_filter(1) if ctx.v_filter(1) else None

        to_var = var_to_text(ctx.VAR()[-3])
        from_var = var_to_text(ctx.VAR()[-2])

        start_nodes: SetInt | None = None
        final_nodes: SetInt | None = None

        if vf1:
            var = var_to_text(vf1.VAR())
            if var == from_var:
                start_nodes = self.visitV_filter(vf1)
            elif var == to_var:
                final_nodes = self.visitV_filter(vf1)

        if vf2:
            var = var_to_text(vf2.VAR())
            if var == from_var:
                start_nodes = self.visitV_filter(vf2)
            elif var == to_var:
                final_nodes = self.visitV_filter(vf2)

        q: FA | RSM = self.visit(ctx.expr())
        g: Graph = self.context.lookup(var_to_text(ctx.VAR()[-1]))

        args = (q, g, start_nodes, final_nodes)
        res: SetIntPair = (
            cfpq_with_gll(*args)
            if type_assertion(Type.RSM, q)
            else cfpq_with_matrix(*args)
        )
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
        return self.visitExpr(ctx.expr())
