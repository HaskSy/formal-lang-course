from project.task11.notgraphql.notgraphqlLexer import notgraphqlLexer
from project.task11.notgraphql.notgraphqlParser import notgraphqlParser
from project.task11.notgraphql.notgraphqlListener import notgraphqlListener

from antlr4 import ParserRuleContext, CommonTokenStream
from antlr4.InputStream import InputStream


class NodeCountListener(notgraphqlListener):

    def __init__(self) -> None:
        super(notgraphqlListener, self).__init__()
        self.count = 0

    def enterEveryRule(self, ctx):
        self.count += 1


class StringifyListener(notgraphqlListener):
    res = ""

    def __init__(self):
        super(notgraphqlListener, self).__init__()

    def enterEveryRule(self, rule):
        self.res += rule.getText()


def prog_to_tree(program: str) -> tuple[ParserRuleContext, bool]:
    parser = notgraphqlParser(CommonTokenStream(notgraphqlLexer(InputStream(program))))
    prog = parser.prog()
    correct = parser.getNumberOfSyntaxErrors() == 0
    return prog, correct


def nodes_count(tree: ParserRuleContext) -> int:
    listener = NodeCountListener()
    tree.enterRule(listener)
    return listener.count


def tree_to_prog(tree: ParserRuleContext) -> str:
    listener = StringifyListener()
    tree.enterRule(listener)
    return listener.res
