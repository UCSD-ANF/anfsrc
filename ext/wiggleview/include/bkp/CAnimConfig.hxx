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
  
	Animconfig.h :
	
	  This class provides methods to load cameras and the
	  geometry of the scene. By default 'StereoCameras.iv' 
	  is used to load the cameras. 
	  
		
*********************************************************************/


#ifndef _ANIMCONFIG_H
#define _ANIMCONFIG_H

#pragma warning(disable:4275)
#pragma warning(disable:4251)
#include <Inventor/SbString.h>
#include <Inventor/nodes/SoPerspectiveCamera.h>
#include <Inventor/nodes/SoSeparator.h>
#include <Inventor/nodes/SoBlinker.h>
#include <Inventor/nodes/SoTranslation.h>
#include <Inventor/nodes/SoText2.h>
#include <iostream>
#include <strstream>
#include <assert.h>
#include <string>
#include <vector>
using namespace std;

class AnimConfig {
	
public:

	// Constructor : give the model and the configuration file
	AnimConfig(const SbString&, const SbString& cameras);

	// Destructor
	virtual ~AnimConfig();
	
	// return leftCamera
	SoPerspectiveCamera* getLeftCamera();

	// return rightCamera
	SoPerspectiveCamera* getRightCamera();

	// load cameras
	void loadCameras(SoGroup*, SoGroup*);

	// load data
	void loadGeometry(int*, int*);

	// return the display mode LEFT,RIGHT or BOTH
	//SbString getDisplayMode();

	// return the frame rate NORMAL or FAST
	//SbString getFrameRate();

	// return ORIGIN or MASS
	//SbString getBindCenter();

	// return ON or OFF
	//SbString getTextDisplay();

	// return a blinker
	SoBlinker* loadFiles(const float&, const SbViewportRegion&);

	// return a blinker that contains the file names
	SoBlinker* getTextBlinker();

	//
	SoTransform* normalize(SoNode*, const SbViewportRegion&);

	// normalize the shapes
	SoTransform* scaleShapes(SoGroup*, const SbViewportRegion&, SbBox3f&, SbVec3f&);

	vector<string> getFileNames();
	
private:

	SbString m_cameras;
	SbString m_config;
	SbString m_displayMode;
	SbString m_frameRate;
	SbString m_bindCenter;
	SbString m_textDisplay;
	SoPerspectiveCamera* m_leftCam;
	SoPerspectiveCamera* m_rightCam;
	SoSeparator* m_configSeparator;
	SoBlinker* textBlinker;
	vector<string> m_fileNames;
};

#endif
