from antlr4 import InputStream, CommonTokenStream

from project.task11.notgraphql.notgraphqlLexer import notgraphqlLexer
from project.task11.notgraphql.notgraphqlParser import notgraphqlParser

from project.task12.type_checker import TypeCheckVisitor, TypeContext
from project.task12.interpreter import InterpreterVisitor


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
    except Exception as e:
        print(e)
        return False


def exec_program(program: str) -> dict[str, set[tuple]]:
    input_stream = InputStream(program)
    lexer = notgraphqlLexer(input_stream)
    stream = CommonTokenStream(lexer)
    parser = notgraphqlParser(stream)
    tree = parser.prog()

    visitor = TypeCheckVisitor()
    context: TypeContext = visitor.visit(tree)

    interpreterVisitor = InterpreterVisitor(context)
    return interpreterVisitor.visit(tree)
