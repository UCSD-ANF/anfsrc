/******************************************************************
 * ImmersaView
 * Copyright (C) 2003 Electronic Visualization Laboratory,
 * all rights reserved
 * By Atul Nayak, Chris Scharver, Vikas Chowdhry, Andrew Johnson, Jason Leigh
 * University of Illinois at Chicago
 *
 * This publication and its text and code may not be copied for commercial
 * use without the express written permission of the University of Illinois
 * at Chicago.
 * The contributors disclaim any representation of warranty: use this
 * code at your own risk.
 * Direct questions, comments etc to cavern@evl.uic.edu
 ******************************************************************/
#ifndef _CSEARCH_HXX
#define _CSEARCH_HXX

#include "common.h"
#include "CUtil.h"

class CSearch
{
public :

	CSearch();
	CSearch(string);
	CSearch(SoSeparator *);
	~CSearch();

	void get(string, string&);
	void get(string, float&);
	void get(string, int&);
	void get(string, long&);
	void get(string, char&);
	void get(string, float*);
	void get(string, int*);
	SoSeparator* get(string);

protected:

	SoSeparator *root;

};
#endif
