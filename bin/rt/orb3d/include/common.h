/******************************************************************
 * Seismoglyph
 * Copyright (C) 2003 Electronic Visualization Laboratory,
 * all rights reserved
 * By Atul Nayak, Andrew Johnson, Jason Leigh
 * University of Illinois at Chicago
 *
 * This publication and its text and code may not be copied for commercial
 * use without the express written permission of the University of Illinois
 * at Chicago.
 * The contributors disclaim any representation of warranty: use this
 * code at your own risk.
 * Direct questions, comments etc to cavern@evl.uic.edu
 ******************************************************************/
#ifndef _COMMON_HXX
#define _COMMON_HXX

#pragma warning(disable:4275)
#pragma warning(disable:4251)
//#include <Inventor/SoDB.h>
#include <Inventor/SoInput.h>
#include <Inventor/SoSceneManager.h>
#include <Inventor/nodes/SoCylinder.h>
#include <Inventor/nodes/SoCone.h>
#include <Inventor/nodes/SoCube.h>
#include <Inventor/nodes/SoDirectionalLight.h>
#include <Inventor/nodes/SoDrawStyle.h>
#include <Inventor/nodes/SoSeparator.h>
#include <Inventor/nodes/SoMaterial.h>
#include <Inventor/nodes/SoMaterialBinding.h>
#include <Inventor/nodes/SoPerspectiveCamera.h>
#include <Inventor/nodes/SoRotor.h>
#include <Inventor/nodes/SoShuttle.h>
#include <Inventor/nodes/SoSphere.h>
#include <Inventor/nodes/SoTransform.h>
#include <Inventor/nodes/SoTexture2.h>
#include <Inventor/nodekits/SoShapeKit.h>  
#include <Inventor/nodekits/SoNodeKit.h>
#include <Inventor/nodekits/SoSceneKit.h>
#include <Inventor/nodekits/SoCameraKit.h>
#include <Inventor/nodekits/SoLightKit.h>
#include <Inventor/actions/SoWriteAction.h>
#include <Inventor/fields/SoSFString.h> 
#include <Inventor/nodes/SoFont.h>
#include <Inventor/nodes/SoText3.h>
#include <Inventor/nodes/SoMaterial.h>
#include <Inventor/nodes/SoMaterialBinding.h>
#include <Inventor/nodes/SoSwitch.h>
#include <Inventor/nodes/SoScale.h>
#include <Inventor/manips/SoTrackballManip.h>
#include <Inventor/SoInteraction.h>
#include <Inventor/nodes/SoPointSet.h>
#include <Inventor/nodes/SoLineSet.h>
#include <Inventor/nodes/SoCoordinate3.h> 
#include <Inventor/engines/SoInterpolate.h> 
#include <Inventor/engines/SoInterpolateVec3f.h> 
#include <Inventor/nodes/SoLightModel.h>
#include <Inventor/nodes/SoBaseColor.h> 
#include <Inventor/nodes/SoShapeHints.h>
#include <Inventor/nodes/SoComplexity.h>
#include <Inventor/nodes/SoInfo.h>
#include <Inventor/actions/SoSearchAction.h>
#include <Inventor/engines/SoElapsedTime.h> 
#include <Inventor/nodes/SoText2.h> 
#include <Inventor/nodes/SoAsciiText.h>
#include <Inventor/nodes/SoAnnotation.h> 
#include <Inventor/nodes/SoBlinker.h>
#include <Inventor/actions/SoGetBoundingBoxAction.h>
#include <Inventor/actions/SoGLRenderAction.h>
#include <Inventor/nodes/SoPickStyle.h>
#include <Inventor/nodes/SoSelection.h>
#include <Inventor/events/SoMouseButtonEvent.h>
#include <Inventor/nodes/SoEventCallback.h>
#include <Inventor/SoPickedPoint.h>
#include <Inventor/nodes/SoTriangleStripSet.h>
#include <Inventor/nodes/SoIndexedFaceSet.h> 
#include <Inventor/fields/SoMFInt32.h> 

#ifdef WIN32
#include <glut.h>
#else
#include <GL/glut.h>
#endif
//#include <simage.h>
#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <list>
#include <strstream>
#include <stdlib.h>
//#include "CUtil.h"
using namespace std;

static const int X = 0;
static const int Y = 1;


const float IV_SCALE_FACTOR        = 0.1f;
const float IV_PAN_FACTOR          = 0.01f;
const float IV_ROTATE_FACTOR  = 2.0f;
const float IV_SPIN_FACTOR = 0.01f;
const float AUTO_SPIN_MIN       = 0.02f;
const float IV_PLAYBACK_FACTOR     = 0.1f;
const float IV_DUMMY = 0.0f;

const float GLYPH_SCREEN_SIZE    = 8.;
const float GLYPH_NSCREEN_CENTER = -2.5;
const float GLYPH_ESCREEN_CENTER = -3.;
const float GLYPH_ZSCREEN_CENTER = -3.5;
//const float GLYPH_SCREEN_LEFT    = -4.;
const float GLYPH_SCREEN_LEFT    = -5.;
const int   MAX_SAMPLES_DRAWN = 1200;
#define SEISMOGLYPHS_VERSION "0.3 - Feb 09, 2005"
#define ESCAPE  0x1B
#define ENTER   0x0a

#ifndef PI
#define PI 3.14159265358979323
#endif

enum fileType {
	SACASCII,
	TRINETSCEC
};

//SoSphere * sphere = new SoSphere;
#endif
