/******************************************************************
 * ImmersaView
 * Copyright (C) 2002 Electronic Visualization Laboratory,
 * all rights reserved
 * By Atul Nayak, Chris Scharver, Vikas Chowdry, Andrew Johnson, Jason Leigh
 * University of Illinois at Chicago
 *
 * This publication and its text and code may not be copied for commercial
 * use without the express written permission of the University of Illinois
 * at Chicago.
 * The contributors disclaim any representation of warranty: use this
 * code at your own risk.
 * Direct questions, comments etc to cavern@evl.uic.edu
 ******************************************************************/

#include "CAnimControl.hxx"
//#include <assert.h>
//#include <iostream.h>

AnimControl::AnimControl(SoBlinker* blinker)
: m_blinker(blinker)
{
}

AnimControl::~AnimControl()
{
}

void
AnimControl::animateFaster()
{
	assert(m_blinker);
	float speed = m_blinker->speed.getValue();
	if (speed < 5.0f)
		speed += 0.1f;
#ifdef DEBUG
	cout<<"Speed = "<<speed<<endl;
#endif
	m_blinker->speed.setValue(speed);
}

void
AnimControl::animateSlower()
{
	assert(m_blinker);
	float speed = m_blinker->speed.getValue();
	if (speed > 0.2f)
		speed -= 0.1f;
#ifdef DEBUG
	cout<<"Speed = "<<speed<<endl;
#endif
	m_blinker->speed.setValue(speed);
}

void
AnimControl::next()
{
	assert(m_blinker);
	int theChild = m_blinker->whichChild.getValue();
	if (theChild == (m_blinker->getNumChildren() - 1))
		theChild = 0;
	else
		theChild++;
	m_blinker->whichChild.setValue(theChild);
}

void
AnimControl::previous()
{
	assert(m_blinker);
	int theChild = m_blinker->whichChild.getValue();
	if (theChild == 0)
		theChild = m_blinker->getNumChildren() - 1;
	else
		theChild--;
	m_blinker->whichChild.setValue(theChild);
}

void
AnimControl::setSpeed(const float& speed)
{
	assert(m_blinker);
	m_blinker->speed.setValue(speed);
}

void
AnimControl::start()
{
	assert(m_blinker);
	m_blinker->on.setValue(TRUE);
}

void
AnimControl::stop()
{
	assert(m_blinker);
	m_blinker->on.setValue(FALSE);
}

void
AnimControl::reset()
{
	assert(m_blinker);
	m_blinker->on.setValue(FALSE);
	m_blinker->whichChild.setValue(0);
}

void
AnimControl::toggleAnimation()
{
	assert(m_blinker);
	if (m_blinker->on.getValue() == TRUE)
		m_blinker->on.setValue(FALSE);
	else
		m_blinker->on.setValue(TRUE);
}

bool
AnimControl::isOn()
{
	return m_blinker->on.getValue();
}

int 
AnimControl::getCurrentChild()
{
	return 	m_blinker->whichChild.getValue();
}

void 
AnimControl::switchTo(int val)
{
	m_blinker->whichChild.setValue(val);
}
