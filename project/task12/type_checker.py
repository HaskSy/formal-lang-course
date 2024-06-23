from enum import Enum

from antlr4 import InputStream, CommonTokenStream

from notgraphqlLexer import notgraphqlLexer
from notgraphqlParser import notgraphqlParser
from notgraphqlListener import notgraphqlListener
from notgraphqlVisitor import notgraphqlVisitor


class Type(Enum):
    INT = "int"
    CHAR = "char"
    FA = "fa"
    RSM = "rsm"
    SET_INT = "set<int>"
    SET_INT_PAIR = "set<int*int>"
    GRAPH = "graph"


class Context:
    def __init__(self):
        self.bindings = {}

    def bind(self, var, typ):
        self.bindings[var] = typ

    def lookup(self, var):
        if var in self.bindings:
            return self.bindings[var]
        else:
            raise Exception(f"Variable '{var}' is not defined")


class TypeCheckVisitor(notgraphqlVisitor):
    def __init__(self):
        self.context = Context()

    def visitProg(self, ctx):
        for stmt in ctx.stmt():
            self.visit(stmt)
        return None

    def visitDeclare(self, ctx):
        var = ctx.VAR().getText()
        self.context.bind(var, Type.GRAPH)
        return None

    def visitBind(self, ctx):
        var = ctx.VAR().getText()
        expr_type = self.visit(ctx.expr())
        self.context.bind(var, expr_type)
        return None

    def visitAdd(self, ctx):
        var = ctx.VAR().getText()
        self.context.lookup(var)
        self.visit(ctx.expr())
        return None

    def visitRemove(self, ctx):
        var = ctx.VAR().getText()
        self.context.lookup(var)
        self.visit(ctx.expr())
        return None

    def visitExpr(self, ctx):
        if ctx.NUM():
            return Type.INT
        elif ctx.CHAR():
            return Type.CHAR
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

    def visitEdge_expr(self, ctx):
        return Type.FA

    def visitSet_expr(self, ctx):
        elem_types = [self.visit(expr) for expr in ctx.expr()]
        if all(t == Type.INT for t in elem_types):
            return Type.SET_INT
        else:
            raise Exception("Set expression contains non-integer elements")

    def visitRegexp(self, ctx):
        if ctx.getChildCount() == 1:
            if ctx.CHAR():
                return Type.CHAR
            elif ctx.VAR():
                return self.context.lookup(ctx.VAR().getText())
        elif ctx.getChildCount() == 2:
            if ctx.regexp():
                return self.visit(ctx.regexp())
            elif ctx.range():
                return self.visit(ctx.range())
        elif ctx.getChildCount() == 3:
            left = self.visit(ctx.regexp(0))
            right = self.visit(ctx.regexp(1))
            op = ctx.getChild(1).getText()
            if op == "|":
                if left == Type.FA and right == Type.FA:
                    return Type.FA
                elif (
                    (left == Type.FA and right == Type.RSM)
                    or (left == Type.RSM and right == Type.FA)
                    or (left == Type.RSM and right == Type.RSM)
                ):
                    return Type.RSM
                else:
                    raise Exception("Invalid union operation types")
            elif op == ".":
                if left == Type.FA and right == Type.FA:
                    return Type.FA
                elif (
                    (left == Type.FA and right == Type.RSM)
                    or (left == Type.RSM and right == Type.FA)
                    or (left == Type.RSM and right == Type.RSM)
                ):
                    return Type.RSM
                else:
                    raise Exception("Invalid concatenation operation types")
            elif op == "&":
                if left == Type.FA and right == Type.FA:
                    return Type.FA
                elif (left == Type.FA and right == Type.RSM) or (
                    left == Type.RSM and right == Type.FA
                ):
                    return Type.RSM
                else:
                    raise Exception("Invalid intersection operation types")
        raise Exception("Unknown regular expression type")

    def visitRange(self, ctx):
        return Type.INT

    def visitSelect(self, ctx):
        vf1 = ctx.v_filter(0)
        vf2 = ctx.v_filter(1)
        ret = ctx.VAR(0)
        v1 = ctx.VAR(1)
        v2 = ctx.VAR(2)
        g = ctx.VAR(3)
        q = ctx.expr()

        q_type = self.visit(q)
        ret_type = self.context.lookup(ret.getText())

        if vf1:
            self.visit(vf1)
        if vf2:
            self.visit(vf2)

        if q_type in [Type.FA, Type.RSM]:
            if ret_type == Type.INT:
                return Type.SET_INT
            elif ret_type == Type.INT_PAIR:
                return Type.SET_INT_PAIR
            else:
                raise Exception("Invalid return type in select query")
        else:
            raise Exception("Invalid query type in select statement")

    def visitV_filter(self, ctx):
        expr_type = self.visit(ctx.expr())
        if expr_type != Type.SET_INT:
            raise Exception("Filter expression must be of type set<int>")
        return Type.SET_INT


def main(input_text):
    input_stream = InputStream(input_text)
    lexer = notgraphqlLexer(input_stream)
    stream = CommonTokenStream(lexer)
    parser = notgraphqlParser(stream)
    tree = parser.prog()

    visitor = TypeCheckVisitor()
    visitor.visit(tree)


if __name__ == "__main__":
    input_text = """
    let a is graph
    let b = [1, 2, 3]
    let c = ("a", 1, "b")
    let c = a | b
    """
    main(input_text)
