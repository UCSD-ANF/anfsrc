#ifndef _DSCONST_H_
#define _DSCONST_H_

/*
 * This file contains datascope constants
 */

#define dbINVALID		    -102
#define INVALID_DBPTR 	{dbINVALID, dbINVALID, dbINVALID, dbINVALID} 

#define dbCOUNT -301
#define dbDATABASE_COUNT -302	       
#define dbTABLE_COUNT -303	      
				        
#define dbFIELD_COUNT -304	       
#define dbRECORD_COUNT -305	      
#define dbDESCRIPTION -306
#define dbSCHEMA_DESCRIPTION -307    
#define dbDATABASE_DESCRIPTION -308 
#define dbTABLE_DESCRIPTION -309   
#define dbFIELD_DESCRIPTION -310  
#define dbDETAIL -311
#define dbSCHEMA_DETAIL -312	       
#define dbDATABASE_DETAIL -313	      
#define dbTABLE_DETAIL -314	     
#define dbFIELD_DETAIL -315	    
#define dbNAME -316
#define dbSCHEMA_NAME -317	       
#define dbDATABASE_NAME -318	      
#define dbTABLE_NAME -319	     
#define dbFIELD_NAME -320	    
#define dbTABLE_PRESENT -321
#define dbSIZE -322
#define dbTABLE_SIZE -323	   
#define dbFIELD_SIZE -324	  
#define dbTYPE -325
#define dbFORMAT -326
#define dbFIELD_UNITS -327
#define dbFIELD_TYPE -328	  
#define dbTABLE_FILENAME   -329
#define dbDBPATH -330
#define dbTABLE_DIRNAME -331
#define dbPRIMARY_KEY -332
#define dbALTERNATE_KEY -333
#define dbFOREIGN_KEYS -334
#define dbUNIQUE_ID_NAME -336
#define dbSCHEMA_DEFAULT -338

#define dbFIELD_RANGE -341
#define dbVIEW_TABLE_COUNT -342
#define dbRECORD_SIZE -343
#define dbFIELD_FORMAT -344
#define dbFIELD_INDEX -345
#define dbTABLE_ADDRESS -346

#define dbTABLE_FIELDS -347
#define dbFIELD_TABLES -348
#define dbVIEW_TABLES -349
#define dbLINK_FIELDS -350
#define dbSCHEMA_FIELDS -351
#define dbTABLE_IS_WRITABLE -352
#define dbTABLE_IS_WRITEABLE -352
#define dbTABLE_IS_VIEW -353
#define dbFIELD_BASE_TABLE -354
#define dbTABLE_IS_TRANSIENT -355
#define dbTIMEDATE_NAME -356
#define dbDATABASE_FILENAME -357
#define dbSCHEMA_TABLES -358
#define dbDATABASE_IS_WRITABLE -359
#define dbDATABASE_IS_WRITEABLE -359
#define dbLASTIDS -360
#define dbIDSERVER -361
#define dbLOCKS	-362
#define dbSCHEMA_LIST -363
#define dbTABLE_IS_ADDABLE -364


#define dbALL			-501
#define dbSCRATCH		-504
#define dbNULL			-505

#define dbBOOLEAN	1
#define dbINTEGER		2
#define dbREAL 		3
#define dbTIME		4
#define dbYEARDAY		5
#define dbSTRING		6
#define dbLINK		8

#define dbWAVEFORM	136
#define dbRESPONSE	137

#define dbBFLOAT        138
#define dbBDOUBLE       139
#define dbBSHORT        140
#define dbBINT          141

#define dbDBPTR		142

#define dbOUTER_JOIN 2

#define dbSORT_UNIQUE  2
#define dbSORT_REVERSE 1

#define strREAL     	 166
#define strINTEGER     	 167
#define strNULL     	 168
#define strSTRING     	 169
#define strTIME     	 170
#define strEXPR		 171
#define strFIELD	 172
#define strUNKNOWN	 173

#endif
