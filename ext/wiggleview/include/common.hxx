#ifndef _COMMON_HXX
#define _COMMON_HXX

#pragma warning(disable:4275)
#pragma warning(disable:4251)
#include <Inventor/SoDB.h>
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
#include <Inventor/actions/SoGetBoundingBoxAction.h>
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
#include <Inventor/nodes/SoInfo.h>
#include <Inventor/actions/SoSearchAction.h>
#include <Inventor/engines/SoElapsedTime.h> 
#include <Inventor/nodes/SoText2.h> 
#include <Inventor/nodes/SoAnnotation.h>
#include <Inventor/nodes/SoAsciiText.h>
#include <Inventor/nodes/SoBlinker.h>

#ifdef WIN32
#include <glut.h>
#endif
#include <simage.h>
#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <strstream>
#include <stdlib.h>
#include "CUtil.hxx"
using namespace std;

static const int X = 0;
static const int Y = 1;

#ifndef PI
#define PI 3.14159265358979323
#endif

/* DTOR is single precision for speed */
#define DTOR(r) ((r)*0.01745329f)

//SoSphere * sphere = new SoSphere;
#endif
