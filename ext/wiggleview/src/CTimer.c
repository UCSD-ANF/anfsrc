#include "CTimer.hxx"

CTimer::CTimer()
{
	myCounter = new SoElapsedTime;

}

CTimer::~CTimer()
{
}

void CTimer::writeInstance(SoOutput* out)
{
	out->openFile("timerOut.iv");
	
	out->closeFile();

}

void CTimer::print()
{
		
}