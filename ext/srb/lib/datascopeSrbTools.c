#include "datascopeSrbTools.h"
 
int 
dbPtr2str(Dbptr* datascopedbPtr,  char *outBuf)
{
    sprintf(outBuf, "%i|%i|%i|%i", 
	    datascopedbPtr->database,
	    datascopedbPtr->table,
            datascopedbPtr->field,
            datascopedbPtr->record);

   return(strlen(outBuf)+1);

}

int
str2dbPtr(char * inBuf, Dbptr*   datascopedbPtr) 
{

    char *argv[10];
    int i;

    i = getArgsFromString (inBuf,argv,DSDELIM,DSESC);
    if (i < 4) {
	datascopedbPtr->database =  dbINVALID;
	datascopedbPtr->table =  dbINVALID;
	datascopedbPtr->field =  dbINVALID;
	datascopedbPtr->record =  dbINVALID;
	return(i);
    }
    datascopedbPtr->database = atoi(argv[0]);
    datascopedbPtr->table =  atoi(argv[1]);
    datascopedbPtr->field =  atoi(argv[2]);
    datascopedbPtr->record =  atoi(argv[3]);
    return(0);

}

int
unescapeDelimiter(char *inOutStr, char del, char esc)
{
    int  i,j,l;
    l = strlen(inOutStr);
    for (i =0, j=0; i <= l ;i++,j++) {
	if (inOutStr[i] == esc && inOutStr[i+1] == del)
	    i++;
	inOutStr[j] = inOutStr[i];
    }
    return(0);

}

int
escapeDelimiter(char *inStr, char *outStr, char del, char esc)
{
    int i,j,l;
    l = strlen(inStr);
    for (i =0, j=0; i <= l ;i++,j++) {
	if (inStr[i] == del) {
	    outStr[j] = esc;
	    j++;
	}
	outStr[j] = inStr[i];
    }
}

Tbl *
str2dbTable( char *inStr )
{
	Tbl	*tbl;
	char	*strings[MAX_PROC_ARGS_FOR_DS];
	int	nstrings;
	int	istring;

	nstrings = getArgsFromString( inStr, strings, DSDELIM, DSESC );
	
	tbl = newtbl( 0 );

	for( istring = 0; istring < nstrings; istring++ ) {
		
		pushtbl( tbl, strdup( strings[istring] ) );	
	}

	return tbl;
}

Arr *
str2dbArray( char *inStr )
{
	Arr	*arr;
	char	*strings[MAX_PROC_ARGS_FOR_DS];
	char	*key;
	char	*val;
	int	nstrings;
	int	istring;

	arr = newarr( 0 );

	nstrings = getArgsFromString( inStr, strings, DSDELIM, DSESC );

	if( nstrings % 2 != 0 ) {

		return arr;
	}

	for( istring = 0; istring < nstrings; istring++ ) {
		
		key = strings[istring++];
		val = strings[istring];
		setarr( arr, key, val );
	}

	return arr;
}

int
dbTable2str(Tbl *inTbl, char *outStr) 
{
    int i,j;
    char *tp, *tp1;
    char del[2];

    del[0] = DSDELIM;
    del[1] = '\0';
    j = maxtbl(inTbl);
    *outStr ='\0';
    if (j <= 0)
	return(j);
    tp = gettbl(inTbl, 0);
    strcat(outStr,tp);
    for (i = 1; i < j ; i++) {
	tp = gettbl(inTbl, i);
	strcat(outStr,del);
	tp1 = (char *)(outStr + strlen(outStr));
	escapeDelimiter(tp,tp1,DSDELIM,DSESC);
    }
    return(0);
}

int
dbArray2str(Arr *inArr, char *outStr)
{
/* array value is considered to be strings */
    Tbl *inTbl;
    int i,j;
    char *tp, *tp1;
    char del[2];

    del[0] = DSDELIM;
    del[1] = '\0';
    inTbl = keysarr(inArr);
    j = maxtbl(inTbl);
    *outStr ='\0';
    if (j <= 0)
        return(j);
    tp = gettbl(inTbl, 0);
    strcat(outStr,tp);
    tp1 = getarr(inArr,tp);
    strcat(outStr,del);
    tp = (char *)(outStr + strlen(outStr));
    escapeDelimiter(tp1,tp,DSDELIM,DSESC);
    for (i = 1; i < j ; i++) {
        tp = gettbl(inTbl, i);
        strcat(outStr,del);
        tp1 = (char *)(outStr + strlen(outStr));
        escapeDelimiter(tp,tp1,DSDELIM,DSESC);
	tp1 = getarr(inArr,tp);
	strcat(outStr,del);
        tp = (char *)(outStr + strlen(outStr));
        escapeDelimiter(tp1,tp,DSDELIM,DSESC);
    }
    return(0);
}

/* Return a newly allocated string with escaped arguments */
char *
putArgsToString( char del, char esc, int nargs, ... )
{
	va_list	ap;
	void	*vstack = 0;
	char	del_str[2];
	char	*input_arg;
	char	*arg;
	int	iarg;
	
	del_str[0] = del;
	del_str[1] = 0;

	va_start( ap, nargs );

	for( iarg = 0; iarg < nargs; iarg++ ) {
 
		if( ( input_arg = va_arg( ap, char * ) ) == NULL ) {

			allot( char *, arg, 2 );

			strcpy( arg, "" );

		} else {

			allot( char *, arg, 2 * strlen( input_arg ) );

			escapeDelimiter( input_arg, arg, del, esc );
		}

		pushstr( &vstack, arg );

		if( iarg != nargs - 1 ) {

			pushstr( &vstack, del_str );
		}

		free( arg );
	}

	va_end( ap );

	return popstr( &vstack, 1 );
}

/* Realloc a string, adding more escaped arguments */
void
addArgsToString( char **string, char del, char esc, Tbl *args )
{
	void	*vstack = 0;
	char	del_str[2];
	char	*input_arg;
	char	*arg;
	int	iarg;

	del_str[0] = del;
	del_str[1] = 0;

	if( *string != NULL ) {
		
		pushstr( &vstack, *string );
		
		if( maxtbl( args ) > 0 ) {

			pushstr( &vstack, del_str );
		}
		
		free( *string );
	}

	for( iarg = 0; iarg < maxtbl( args ); iarg++ ) {

		input_arg = gettbl( args, iarg );

		allot( char *, arg, 2 * strlen( input_arg ) );

		escapeDelimiter( input_arg, arg, del, esc );

		pushstr( &vstack, arg );

		if( iarg != maxtbl( args ) - 1 ) {

			pushstr( &vstack, del_str );
		}

		free( arg );
	}

	*string = popstr( &vstack, 1 );

	return;
}

int
getArgsFromString(char *inStr, char *argv[], char del, char esc)
{
    int i,j;
    int iarg;
    char *tmpPtr, *tmpPtr1;
    
    j  = 0;
    tmpPtr = inStr;
    if (*tmpPtr == del) {
	argv[j] = tmpPtr;
	*tmpPtr = '\0';
	tmpPtr = tmpPtr + 1;
	j++;
    }
    tmpPtr1 = tmpPtr;
    for (i  = j; i < MAX_PROC_ARGS_FOR_DS ; i++) {
	argv[i] = tmpPtr;
	if ((tmpPtr1 = strchr(tmpPtr1,del)) != NULL) {
	    if ( *(tmpPtr1 - 1) != esc ){
		*tmpPtr1 =  '\0';
		tmpPtr = ++tmpPtr1;
	    }
	    else { 
		i--; 
		strcpy(tmpPtr1-1, tmpPtr1++);
	    }
	}
	else 
	    break;
    }
    for( iarg = 0; iarg <= i; iarg++ ) {
	unescapeDelimiter( argv[iarg], del, esc );
    }
    return(i+1);
}

