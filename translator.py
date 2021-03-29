__author__ = 'Jihun Bae'

import sys
from antlr4 import *
from antlr4.InputStream import InputStream
from AdaToCLexer import AdaToCLexer
from AdaToCParser import AdaToCParser
from MyListener import MyListener
from MyWriter import MyWriter


def main(argv):
    input_stream = FileStream(argv[1])
    lexer = AdaToCLexer(input_stream)
    token_stream = CommonTokenStream(lexer)
    parser = AdaToCParser(token_stream)
    tree = parser.decl()

    lisp_tree_str = tree.toStringTree(recog=parser)
    print(lisp_tree_str)

    walker = ParseTreeWalker()
    mylistener = MyListener()
    walker.walk(mylistener, tree)
    writer = MyWriter(mylistener)
    writer.fileWrite()


if __name__ == "__main__":
    main(sys.argv)
