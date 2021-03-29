grammar AdaToC;

decl:   (var_decl | proc_decl | lib_decl)+  ;

var_decl    :   ID  ':' var_type ';'
            |   ID  ':' var_type ';'
            |   ID  ':' var_type expr ';'
            ;

proc_decl   :   'procedure' ID '('? proc_param* ')'? 'is' compound_stmt ';'  ;
func_decl   :   'function' ID '(' func_params ')' 'is' 'return' var_type 'is' compound_stmt ';'  ;

lib_decl    :   'with' ('Ada.' ID) (', Ada.' ID)* ';'
            |   'use' ('Ada.' ID) (', Ada.' ID)* ';'
            ;

proc_param  :   (ID ':' ('in' | 'out') var_type ';'?)  ;

func_params :   (ID (',' ID)* ':' var_type ';')+ ;

var_type    :   'INTEGER'
            |   'FLOAT'
            |   'STRING'
            ;

compound_stmt   :   (var_decl | proc_decl | func_decl)* 'begin' stmt* ('declare'? (proc_decl | func_decl)* 'end;'?) stmt* 'end' ID ;

stmt    :   expr_stmt   ;

expr_stmt   :   expr ';'    ;

expr    :   NUM
        |   '(' expr ')'
        |   expr '..' expr
        |   ':=' expr
        |   expr ':=' expr
        |   '"'  expr '"'
        |   ID
        |   ID '[' expr ']'
        |   left=expr '+' right=expr
        |   expr '-' expr
        |   expr '*' expr
        |   expr '/' expr
        |   expr '=' expr
        ;

ID  :   [a-zA-Z][a-zA-Z0-9_!~]*  ;
WS  :   [ \t\r\n]+ -> skip  ;
NUM :   [-]?[0-9]+(.?[0-9]+)*  ;