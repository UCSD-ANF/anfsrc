/** Lexical analyzer for SQL.
 *
 *  Portions Copyright (c) 1990, 1992 O'Reilly & Associates, Inc.
 *  Portions Copyright (c) 2004 by the Regents of the University of California
 *
 *  Adapted for use with Antelope/dbsql on 2004-07-19 by Tobin Fricke, IGPP;
 *  contact info: <tobin@splorg.org> <http://splorg.org/people/tobin>.
 *
 *  This parser is based on code from the O'Reilly book, "Lex & Yacc," second
 *  edition, by John R. Levine, Tony Mason, and Doug Brown (ISBN 1-56592-000-7).
 *

O'Reilly has a quite liberal policy on the re-use of example code from
their books:
  
  You can use and redistribute example code from our books for any
  non-commercial purpose (and most commercial purposes) as long as you
  acknowledge their source and authorship. The source of the code should
  be noted in any documentation as well as in the program code itself (as a
  comment). The attribution should include author, title, publisher, and ISBN.
  
  [http://www.oreilly.com/pub/a/oreilly/ask_tim/2001/codepolicy.html]

*/


%{
#include <string.h>
#include "sql.tab.h"

int lineno = 1;
void yyerror(char *s);
%}

%option noyywrap
%e 1200

%%

  /*
 
  foreach word (\
	ALL AMMSC ANY AS ASC AUTHORIZATION BETWEEN BY \
 	CHARACTER CHECK CLOSE COMMIT CONTINUE CREATE CURRENT \
 	CURSOR DECIMAL DECLARE DEFAULT DELETE DESC DISTINCT DOUBLE \
 	ESCAPE EXISTS FETCH FLOAT FOR FOREIGN FOUND FROM GOTO \
 	GRANT GROUP HAVING IN INDICATOR INSERT INTEGER INTO \
 	IS KEY LANGUAGE LIKE MODULE NULLX NUMERIC OF ON \
 	OPEN OPTION ORDER PRECISION PRIMARY PRIVILEGES PROCEDURE \
 	PUBLIC REAL REFERENCES ROLLBACK SCHEMA SELECT SET \
 	SMALLINT SOME SQLCODE SQLERROR TABLE TO UNION \
 	UNIQUE UPDATE USER VALUES VIEW WHENEVER WHERE WITH WORK \
 	COBOL FORTRAN PASCAL PLI C ADA)
    echo $word 	{ return $word\; }
  end
  */

ALL { return ALL; }
AMMSC { return AMMSC; }
ANY { return ANY; }
AS { return AS; }
ASC { return ASC; }
AUTHORIZATION { return AUTHORIZATION; }
BETWEEN { return BETWEEN; }
BY { return BY; }
CHARACTER { return CHARACTER; }
CHECK { return CHECK; }
CLOSE { return CLOSE; }
COMMIT { return COMMIT; }
CONTINUE { return CONTINUE; }
CREATE { return CREATE; }
CURRENT { return CURRENT; }
CURSOR { return CURSOR; }
DECIMAL { return DECIMAL; }
DECLARE { return DECLARE; }
DEFAULT { return DEFAULT; }
DELETE { return DELETE; }
DESC { return DESC; }
DISTINCT { return DISTINCT; }
DOUBLE { return DOUBLE; }
ESCAPE { return ESCAPE; }
EXISTS { return EXISTS; }
FETCH { return FETCH; }
FLOAT { return FLOAT; }
FOR { return FOR; }
FOREIGN { return FOREIGN; }
FOUND { return FOUND; }
FROM { return FROM; }
GOTO { return GOTO; }
GRANT { return GRANT; }
GROUP { return GROUP; }
HAVING { return HAVING; }
IN { return IN; }
INDICATOR { return INDICATOR; }
INSERT { return INSERT; }
INTEGER { return INTEGER; }
INTO { return INTO; }
IS { return IS; }
KEY { return KEY; }
LANGUAGE { return LANGUAGE; }
LIKE { return LIKE; }
MODULE { return MODULE; }
NULLX { return NULLX; }
NUMERIC { return NUMERIC; }
OF { return OF; }
ON { return ON; }
OPEN { return OPEN; }
OPTION { return OPTION; }
ORDER { return ORDER; }
PRECISION { return PRECISION; }
PRIMARY { return PRIMARY; }
PRIVILEGES { return PRIVILEGES; }
PROCEDURE { return PROCEDURE; }
PUBLIC { return PUBLIC; }
REAL { return REAL; }
REFERENCES { return REFERENCES; }
ROLLBACK { return ROLLBACK; }
SCHEMA { return SCHEMA; }
SELECT { return SELECT; }
SET { return SET; }
SMALLINT { return SMALLINT; }
SOME { return SOME; }
SQLCODE { return SQLCODE; }
SQLERROR { return SQLERROR; }
TABLE { return TABLE; }
TO { return TO; }
UNION { return UNION; }
UNIQUE { return UNIQUE; }
UPDATE { return UPDATE; }
USER { return USER; }
VALUES { return VALUES; }
VIEW { return VIEW; }
WHENEVER { return WHENEVER; }
WHERE { return WHERE; }
WITH { return WITH; }
WORK { return WORK; }
COBOL { return COBOL; }
FORTRAN { return FORTRAN; }
PASCAL { return PASCAL; }
PLI { return PLI; }
C { return C; }
ADA { return ADA; }

  /* Punctuation */

"=" 	|
"<>" 	|
"<" 	|
">"	|
"<="	|
">="	{ return COMPARISON; }

[-+*/:(),.;]	{ return yytext[0]; }

 /* Names */

[A-Za-z][A-Za-z0-9_]* { return NAME; }

 /* Numbers */

[0-9]+		|
[0-9]+"."[0-9]*	|
"."[0-9]*	{ return INTNUM; }

[0-9]+[eE][+-]?[0-9]+		|
[0-9]+"."[0-9]*[eE][+-]?[0-9]+	|
"."[0-9]*[eE][+-]?[0-9]+	{ return APPROXNUM; }

 /* Strings */

 /* This is how they do it in the Lex&Yacc book. I'd rather use a modal scheme,
    just because it gives the scanner generator more work to do and the C
    programmer less.
 */

'[^'\n]*'	{  int c = input();
		   unput(c);
		   if (c != '\'')	/* The L&Y book has a bug here. */
		     return STRING;
		   else
		     yymore();
		}

'[^'\n]*$	{  yyerror("Unterminated string."); }

 /* Whitespace */

\n		lineno ++;

[ \t\r]+	; /* whitespace */

"--".*		; /* comment*/

 /* Anything else... */

.		yyerror("invalid character");

%%

void yyerror(char *s) {
  printf("%d: %s at %s \n", lineno, s, yytext);
}

extern int yydebug;

int main(int ac, char **av) {
  if (ac > 1 && ( yyin = fopen(av[1], "r")) == NULL) {
    perror(av[1]);
    exit(1);
  }

  yydebug = 1;

  if (! yyparse()) {
    printf("SQL parse succeeded.\n");
  } else {
    printf("SQL parse failed.\n");
  }
 
  return 0;
}
 
