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
 
 /*********************************************************************

  Immersaview : An Open Inventor Viewer for the AGAVE/GeoWall
  
	AnimControl.h :
	
	  This class provides methods to control the playback of the
	  animation.
	  
		
*********************************************************************/

#ifndef _ANIMCONTROL_H
#define _ANIMCONTROL_H

#pragma warning(disable:4275)
#pragma warning(disable:4251)
#include <Inventor/nodes/SoBlinker.h>
#include <iostream>
#include <assert.h>
using namespace std;

class AnimControl
{
public:
	AnimControl(SoBlinker*);
	~AnimControl();
	
	void animateFaster();
	void animateSlower();
	void next();
	void previous();
	void setSpeed(const float&);
	void start();
	void stop();
	void reset();
	void toggleAnimation();
	int getCurrentChild();
	void switchTo(int);
	bool isOn();

	
private:
	SoBlinker* m_blinker;
};

#endif
