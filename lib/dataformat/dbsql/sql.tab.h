/* A Bison parser, made from sql.y, by GNU bison 1.75.  */

/* Skeleton parser for Yacc-like parsing with Bison,
   Copyright (C) 1984, 1989, 1990, 2000, 2001, 2002 Free Software Foundation, Inc.

   This program is free software; you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation; either version 2, or (at your option)
   any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program; if not, write to the Free Software
   Foundation, Inc., 59 Temple Place - Suite 330,
   Boston, MA 02111-1307, USA.  */

/* As a special exception, when this file is copied by Bison into a
   Bison output file, you may use that output file without restriction.
   This special exception was added by the Free Software Foundation
   in version 1.24 of Bison.  */

#ifndef BISON_SQL_TAB_H
# define BISON_SQL_TAB_H

/* Tokens.  */
#ifndef YYTOKENTYPE
# define YYTOKENTYPE
   /* Put the tokens into the symbol table, so that GDB and other debuggers
      know about them.  */
   enum yytokentype {
     NAME = 258,
     STRING = 259,
     INTNUM = 260,
     APPROXNUM = 261,
     OR = 262,
     AND = 263,
     NOT = 264,
     COMPARISON = 265,
     UMINUS = 266,
     ALL = 267,
     AMMSC = 268,
     ANY = 269,
     AS = 270,
     ASC = 271,
     AUTHORIZATION = 272,
     BETWEEN = 273,
     BY = 274,
     CHARACTER = 275,
     CHECK = 276,
     CLOSE = 277,
     COMMIT = 278,
     CONTINUE = 279,
     CREATE = 280,
     CURRENT = 281,
     CURSOR = 282,
     DECIMAL = 283,
     DECLARE = 284,
     DEFAULT = 285,
     DELETE = 286,
     DESC = 287,
     DISTINCT = 288,
     DOUBLE = 289,
     ESCAPE = 290,
     EXISTS = 291,
     FETCH = 292,
     FLOAT = 293,
     FOR = 294,
     FOREIGN = 295,
     FOUND = 296,
     FROM = 297,
     GOTO = 298,
     GRANT = 299,
     GROUP = 300,
     HAVING = 301,
     IN = 302,
     INDICATOR = 303,
     INSERT = 304,
     INTEGER = 305,
     INTO = 306,
     IS = 307,
     KEY = 308,
     LANGUAGE = 309,
     LIKE = 310,
     MODULE = 311,
     NULLX = 312,
     NUMERIC = 313,
     OF = 314,
     ON = 315,
     OPEN = 316,
     OPTION = 317,
     ORDER = 318,
     PRECISION = 319,
     PRIMARY = 320,
     PRIVILEGES = 321,
     PROCEDURE = 322,
     PUBLIC = 323,
     REAL = 324,
     REFERENCES = 325,
     ROLLBACK = 326,
     SCHEMA = 327,
     SELECT = 328,
     SET = 329,
     SMALLINT = 330,
     SOME = 331,
     SQLCODE = 332,
     SQLERROR = 333,
     TABLE = 334,
     TO = 335,
     UNION = 336,
     UNIQUE = 337,
     UPDATE = 338,
     USER = 339,
     VALUES = 340,
     VIEW = 341,
     WHENEVER = 342,
     WHERE = 343,
     WITH = 344,
     WORK = 345,
     COBOL = 346,
     FORTRAN = 347,
     PASCAL = 348,
     PLI = 349,
     C = 350,
     ADA = 351
   };
#endif
#define NAME 258
#define STRING 259
#define INTNUM 260
#define APPROXNUM 261
#define OR 262
#define AND 263
#define NOT 264
#define COMPARISON 265
#define UMINUS 266
#define ALL 267
#define AMMSC 268
#define ANY 269
#define AS 270
#define ASC 271
#define AUTHORIZATION 272
#define BETWEEN 273
#define BY 274
#define CHARACTER 275
#define CHECK 276
#define CLOSE 277
#define COMMIT 278
#define CONTINUE 279
#define CREATE 280
#define CURRENT 281
#define CURSOR 282
#define DECIMAL 283
#define DECLARE 284
#define DEFAULT 285
#define DELETE 286
#define DESC 287
#define DISTINCT 288
#define DOUBLE 289
#define ESCAPE 290
#define EXISTS 291
#define FETCH 292
#define FLOAT 293
#define FOR 294
#define FOREIGN 295
#define FOUND 296
#define FROM 297
#define GOTO 298
#define GRANT 299
#define GROUP 300
#define HAVING 301
#define IN 302
#define INDICATOR 303
#define INSERT 304
#define INTEGER 305
#define INTO 306
#define IS 307
#define KEY 308
#define LANGUAGE 309
#define LIKE 310
#define MODULE 311
#define NULLX 312
#define NUMERIC 313
#define OF 314
#define ON 315
#define OPEN 316
#define OPTION 317
#define ORDER 318
#define PRECISION 319
#define PRIMARY 320
#define PRIVILEGES 321
#define PROCEDURE 322
#define PUBLIC 323
#define REAL 324
#define REFERENCES 325
#define ROLLBACK 326
#define SCHEMA 327
#define SELECT 328
#define SET 329
#define SMALLINT 330
#define SOME 331
#define SQLCODE 332
#define SQLERROR 333
#define TABLE 334
#define TO 335
#define UNION 336
#define UNIQUE 337
#define UPDATE 338
#define USER 339
#define VALUES 340
#define VIEW 341
#define WHENEVER 342
#define WHERE 343
#define WITH 344
#define WORK 345
#define COBOL 346
#define FORTRAN 347
#define PASCAL 348
#define PLI 349
#define C 350
#define ADA 351




#ifndef YYSTYPE
#line 5 "sql.y"
typedef union {
	int intval;
	double floatval;
	char *strval;
	int subtok;
} yystype;
/* Line 1281 of /usr/share/bison/yacc.c.  */
#line 239 "sql.tab.h"
# define YYSTYPE yystype
#endif

extern YYSTYPE yylval;


#endif /* not BISON_SQL_TAB_H */

