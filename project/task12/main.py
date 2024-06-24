from antlr4 import InputStream, CommonTokenStream

from project.task11.notgraphql.notgraphqlLexer import notgraphqlLexer
from project.task11.notgraphql.notgraphqlParser import notgraphqlParser

from project.task12.type_checker import TypeCheckVisitor


def typing_program(program: str) -> bool:
    input_stream = InputStream(program)
    lexer = notgraphqlLexer(input_stream)
    stream = CommonTokenStream(lexer)
    parser = notgraphqlParser(stream)
    tree = parser.prog()

    visitor = TypeCheckVisitor()
    try:
        visitor.visit(tree)
        return True
    except:
        return False
