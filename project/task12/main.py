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
    visitor.visit(tree)
    return True

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

if __name__ == '__main__':
    # program = """
    #     let g1 is graph
    #     add edge (0, "f", 1) to g1
    #     add edge (1, "c", 2) to g1
    #     add edge (1, "g", 3) to g1
    #     add edge (1, "a", 0) to g1
    #     add edge (1, "b", 0) to g1
    #     add edge (1, "f", 1) to g1
    #     add edge (1, "b", 1) to g1
    #     add edge (2, "a", 0) to g1
    #     add edge (4, "h", 0) to g1
    #     add edge (5, "c", 2) to g1
    #     add edge (6, "e", 1) to g1
    #     add edge (7, "a", 1) to g1
    #     
    #     let s2 = "b"
    #     
    #     let r3 = for v in [5, 6] for u in [7] return u, v where u reachable from v in g1 by s2 
    # """
    program = """
   

let g1 is graph
add edge (0, "f", 1) to g1
add edge (0, "d", 0) to g1
add edge (0, "a", 0) to g1
add edge (0, "e", 0) to g1
add edge (0, "a", 0) to g1
add edge (0, "e", 0) to g1
add edge (0, "d", 12) to g1
add edge (0, "e", 6) to g1
add edge (1, "g", 2) to g1
add edge (1, "f", 3) to g1
add edge (2, "e", 0) to g1
add edge (2, "g", 0) to g1
add edge (2, "f", 1) to g1
add edge (2, "g", 3) to g1
add edge (3, "f", 3) to g1
add edge (3, "c", 2) to g1
add edge (3, "d", 0) to g1
add edge (4, "a", 3) to g1
add edge (4, "c", 0) to g1
add edge (5, "d", 0) to g1
add edge (6, "f", 1) to g1
add edge (6, "a", 0) to g1
add edge (6, "c", 2) to g1
add edge (6, "d", 3) to g1
add edge (6, "g", 3) to g1
add edge (6, "d", 17) to g1
add edge (7, "b", 2) to g1
add edge (8, "c", 3) to g1
add edge (8, "g", 3) to g1
add edge (8, "g", 3) to g1
add edge (8, "d", 9) to g1
add edge (8, "h", 0) to g1
add edge (9, "e", 3) to g1
add edge (9, "g", 0) to g1
add edge (9, "f", 0) to g1
add edge (9, "c", 0) to g1
add edge (9, "h", 6) to g1
add edge (9, "h", 17) to g1
add edge (10, "h", 2) to g1
add edge (11, "f", 0) to g1
add edge (13, "h", 9) to g1
add edge (14, "h", 1) to g1
add edge (15, "c", 0) to g1
add edge (16, "h", 3) to g1
add edge (18, "c", 1) to g1

let s12 = "a"
let s3 = s12 . s24 . s35
let s24 = "a"^[0 .. 0] | s24 . "b"
let s35 = "a"^[0 .. 0] | "c" . s35

let r6 = for v in [6] for u in [0, 4, 5, 6, 7, 9, 10, 11, 12, 14, 16, 17, 18] return u, v where u reachable from v in g1 by s3 
    """
    typing_program(program)