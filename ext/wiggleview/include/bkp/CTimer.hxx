#ifndef _CTIMER_HXX
#define _CTIMER_HXX

#include "common.hxx"

class CTimer:public SoElapsedTime
{
public:
	CTimer();
	~CTimer();
	void print();
	void writeInstance(SoOutput*);

protected:

	SoElapsedTime *myCounter;

};

#endif
