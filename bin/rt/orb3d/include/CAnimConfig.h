/******************************************************************
  
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

#include "CSearch.h"

class AnimConfig {
	
public:

	// Constructor : give the model and the configuration file
	AnimConfig(const SbString&, const SbString& cameras);

	AnimConfig(SoSeparator*);
	AnimConfig(const SbString&, const SbString& cameras,SoSeparator*, SoSeparator*);

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

	// return a blinker
	//SoBlinker* loadFiles(const float&, const SbViewportRegion&, SoSeparator*);

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
	string m_frameRate;
	string m_bindCenter;
	string m_textDisplay;
	SoPerspectiveCamera* m_leftCam;
	SoPerspectiveCamera* m_rightCam;
	SoSeparator* m_configSeparator;
	SoBlinker* textBlinker;
	vector<string> m_fileNames;
};

#endif
