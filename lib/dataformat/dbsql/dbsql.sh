#!/bin/tcsh

# This is a helper script that is used in generating the lexer and parser
# for SQL.

# Copyright (c) 2004 by the Regents of the University of California
# Created 2004-07-19 by Tobin Fricke <tobin@splorg.org> at IGPP.

set terminals =  ();

set nonterminals = (COMPARISON, NAME, APPROXNUM, STRING);

