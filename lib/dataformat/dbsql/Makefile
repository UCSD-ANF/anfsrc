
# Quick hack to generate sources

LEX = flex 
YACC = bison -dvtg

sql: lex.yy.o sql.tab.o
	$(CC) lex.yy.o sql.tab.o -o sql

sql.tab.c: sql.y
	$(YACC) -d sql.y

sql.tab.o: sql.tab.c
	$(CC) -c sql.tab.c

lex.yy.c: sql.l sql.tab.c
	$(LEX) sql.l

lex.yy.o: lex.yy.c
	$(CC) -c lex.yy.c 

clean:
	rm *.o sql.tab.c lex.yy.c

# Antelope-style makefile begins here

LIB= libdbsql.a
DLIB=$(LIB:.a=$(DSUFFIX))
INCLUDE= dbsql.h

MAN3= dbsql.3

CLEAN=

cflags=
fflags=
ldflags=
ldlibs=

#include $(ANTELOPEMAKE)
DBG= -g

DIRS=

OBJS= dbsql.o

$(LIB) : $(OBJS)
	$(RM) $@
	$(AR) $(ARFLAGS) $@ $(LORDER) $(OBJS) $(TSORT)
	$(RANLIB) $@

$(DLIB) : $(OBJS)
	$(RM) $@
	$(DLD) $(DLDFLAGS) -o $(DLIB) $(LORDER) $(OBJS) $(TSORT) $(DLDLIBS) 
