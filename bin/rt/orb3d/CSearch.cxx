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
#include "CSearch.h"

CSearch::CSearch()
{}

CSearch::CSearch(string fileName)
{

	//root = loadFile(fileName.c_str(),0);
	root = loadFile(fileName.c_str());
	root->ref();

	//	cout<<root->getRefCount();

	//SoWriteAction writeAction;
	//writeAction.apply(root); //write the entire scene graph to stdout

	
}

CSearch::CSearch(SoSeparator* aRoot)
{
	root = aRoot;
}

CSearch::~CSearch()
{
//	root->unref();
//	if (root)
//		delete root;
}
/*
SoSwitch* CSearch::get(string id)
{
	SoSearchAction mySearchAction;
	mySearchAction.setName(id.c_str());
	mySearchAction.apply(root);
	if (mySearchAction.getPath() == NULL) 
	{
		cerr<<id<<" not found in ";
		exit(-1);
	}
	SoPath *p = new SoPath;
	p = mySearchAction.getPath();
	SoSwitch *aSwitch;
	aSwitch = (SoSwitch*) p->getTail();
	return aSwitch;	
}
*/
SoSeparator* CSearch::get(string id)
{
	SoSearchAction mySearchAction;
	mySearchAction.setName(id.c_str());
	mySearchAction.apply(root);
	if (mySearchAction.getPath() == NULL) 
	{
		cerr<<id<<" not found in ";
		exit(-1);
	}
	SoPath *p = new SoPath;
	p = mySearchAction.getPath();
	SoSeparator *aSep;
	aSep = (SoSeparator*) p->getTail();
//	p->unref();
	return aSep;	
}

void CSearch::get(string id, long &val)
{
	SoSearchAction mySearchAction;
	mySearchAction.setName(id.c_str());
	mySearchAction.apply(root);
	if (mySearchAction.getPath() == NULL) 
	{
		cerr<<id<<" not found in configuration file";
		exit(-1);
	}
	SoPath *p = new SoPath;
	p = mySearchAction.getPath();
	SoInfo* info = (SoInfo*) p->getTail();
	istrstream offStr(info->string.getValue().getString());
	offStr >> val;
//	p->unref();

}

void CSearch::get(string id, int &val)
{
	SoSearchAction mySearchAction;
	mySearchAction.setName(id.c_str());
	mySearchAction.apply(root);
	if (mySearchAction.getPath() == NULL) 
	{
		cerr<<id<<" not found in configuration file";
		exit(-1);
	}
	SoPath *p = new SoPath;
	p = mySearchAction.getPath();
	SoInfo* info = (SoInfo*) p->getTail();
	istrstream offStr(info->string.getValue().getString());
	offStr >> val;
//	p->unref();

}

void CSearch::get(string id, float &val)
{
	SoSearchAction mySearchAction;
	mySearchAction.setName(id.c_str());
	mySearchAction.apply(root);
	if (mySearchAction.getPath() == NULL) 
	{
		cerr<<id<<" not found in configuration file";
		exit(-1);
	}
	SoPath *p = new SoPath;
	p = mySearchAction.getPath();
	SoInfo* info = (SoInfo*) p->getTail();
	istrstream offStr(info->string.getValue().getString());
	offStr >> val;
//	p->unref();

}

void CSearch::get(string id, string &val)
{
	//SoOutput out;
	//out.openFile("out.iv");
	//SoWriteAction writeAction(&out);
	//writeAction.apply(root);
	SoSearchAction mySearchAction;
	mySearchAction.setName(id.c_str());
	mySearchAction.apply(root);
	if (mySearchAction.getPath() == NULL) 
	{
		cerr<<id<<" not found in configuration file";
		exit(-1);
	}
	SoPath *p = new SoPath;
	p = mySearchAction.getPath();
	SoInfo* info = (SoInfo*) p->getTail();
	istrstream offStr(info->string.getValue().getString());
	offStr >> val;
//	p->unref();

}

void CSearch::get(string id, char &val)
{
	SoSearchAction mySearchAction;
	mySearchAction.setName(id.c_str());

//	SoWriteAction writeAction;
//	writeAction.apply(root); 

	mySearchAction.apply(root);
	if (mySearchAction.getPath() == NULL) 
	{
		cerr<<id<<" not found in configuration file";
		exit(-1);
	}
	SoPath *p = new SoPath;
	p = mySearchAction.getPath();
	SoInfo* info = (SoInfo*) p->getTail();
	istrstream offStr(info->string.getValue().getString());
	offStr >> val;
//	p->unref();

}

void CSearch::get(string id, float * val)
{
	SoSearchAction mySearchAction;
	mySearchAction.setName(id.c_str());

//	SoWriteAction writeAction;
//	writeAction.apply(root); 

	mySearchAction.apply(root);
	if (mySearchAction.getPath() == NULL) 
	{
		cerr<<id<<" not found in configuration file";
		exit(-1);
	}
	SoPath *p = new SoPath;
	p = mySearchAction.getPath();
	SoInfo* info = (SoInfo*) p->getTail();
	istrstream offStr(info->string.getValue().getString());
	offStr >> val[0] >>val[1]>>val[2] >> val[3];
//	p->unref();

}

void CSearch::get(string id, int * val)
{
	SoSearchAction mySearchAction;
	mySearchAction.setName(id.c_str());

//	SoWriteAction writeAction;
//	writeAction.apply(root); 

	mySearchAction.apply(root);
	if (mySearchAction.getPath() == NULL) 
	{
		cerr<<id<<" not found in configuration file";
		exit(-1);
	}
	SoPath *p = new SoPath;
	p = mySearchAction.getPath();
	SoInfo* info = (SoInfo*) p->getTail();
	istrstream offStr(info->string.getValue().getString());
	offStr >> val[0] >>val[1];
//	p->unref();

}
