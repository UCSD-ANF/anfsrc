#ifndef _CSEARCH_HXX
#define _CSEARCH_HXX

#include "common.hxx"

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
	void get(string, int*, int);
	SoSwitch* get(string);

protected:

	SoSeparator *root;

};
#endif
