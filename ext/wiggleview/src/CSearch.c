#include "CSearch.hxx"

CSearch::CSearch()
{}

CSearch::CSearch(string fileName)
{
	root = new SoSeparator;

//	cout<<root->getRefCount();
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
{}

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


}

void CSearch::get(string id, string &val)
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
	offStr >> val[0] >>val[1]>>val[2];
}

void CSearch::get(string id, int * val, int len)
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
	for (int i = 0; i < len; i++)
		offStr >> val[i];
		//offStr >> val[0] >>val[1]>>val[2];

}
