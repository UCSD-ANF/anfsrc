/******************************************************************
 * ImmersaView
 * Copyright (C) 2003 Electronic Visualization Laboratory,
 * all rights reserved
 * By Atul Nayak, Chris Scharver, Vikas Chowdhry, Andrew Johnson, Jason Leigh
 * University of Illinois at Chicago
 *
 * This publication and its text and code may not be copied for commercial
 * use without the express written permission of the University of Illinois
 * at Chicago.
 * The contributors disclaim any representation of warranty: use this
 * code at your own risk.
 * Direct questions, comments etc to cavern@evl.uic.edu
 ******************************************************************/
#pragma warning(disable:4275)
#pragma warning(disable:4251)

#include <Inventor/SbLinear.h>
#include <Inventor/actions/SoGetBoundingBoxAction.h>
#include <Inventor/nodekits/SoCameraKit.h>
#include <Inventor/nodes/SoBlinker.h>
#include <Inventor/nodes/SoCube.h>
#include <Inventor/nodes/SoFile.h>
#include <Inventor/nodes/SoInfo.h>
#include <Inventor/nodes/SoPerspectiveCamera.h>
#include <Inventor/nodes/SoSeparator.h>
#include <Inventor/nodes/SoTransform.h>
#include <Inventor/nodes/SoDirectionalLight.h>
#include <Inventor/actions/SoSearchAction.h>
#include <Inventor/actions/SoWriteAction.h>

#include "CAnimConfig.h"
#include "CUtil.h"
//#define DEBUG

AnimConfig::AnimConfig(const SbString& filename, const SbString& cameras)
: m_config(filename), m_cameras(cameras)
{
	m_configSeparator = new SoSeparator;
	
	m_configSeparator = loadFile(m_cameras.getString());
	/*SoInput myInput;
	if (!myInput.openFile(m_cameras.getString()))
	{
		cout<<"Error opening file "<<m_cameras.getString()<<endl;
		exit(-1);
	}
	if (!myInput.isValidFile())
	{
		cerr<<"File "<< m_cameras.getString() <<"is not a valid Inventor file"<<endl;
		exit(-1);
	}
	else
		cerr<<"Inventor Version used in File: "<<myInput.getIVVersion()<<endl;
	
	m_configSeparator = SoDB::readAll(&myInput);
	*/
	m_configSeparator->ref();
	
}
AnimConfig::AnimConfig(SoSeparator* stereoCams)
{

	m_configSeparator = new SoSeparator;
	m_configSeparator = stereoCams;
	m_configSeparator->ref();
}
AnimConfig::AnimConfig(const SbString& filename, 
					   const SbString& cameras,
					   SoSeparator *sceneFile, 
					   SoSeparator* stereoCams)
: m_config(filename), m_cameras(cameras)
{
	m_configSeparator = new SoSeparator;
	
	m_configSeparator = stereoCams;
	/*SoInput myInput;
	if (!myInput.openFile(m_cameras.getString()))
	{
		cout<<"Error opening file "<<m_cameras.getString()<<endl;
		exit(-1);
	}
	if (!myInput.isValidFile())
	{
		cerr<<"File "<< m_cameras.getString() <<"is not a valid Inventor file"<<endl;
		exit(-1);
	}
	else
		cerr<<"Inventor Version used in File: "<<myInput.getIVVersion()<<endl;
	
	m_configSeparator = SoDB::readAll(&myInput);
	*/
	m_configSeparator->ref();
	
}


AnimConfig::~AnimConfig()
{
}

SoPerspectiveCamera*
AnimConfig::getLeftCamera()
{
	return m_leftCam;
}

SoPerspectiveCamera*
AnimConfig::getRightCamera()
{
	return m_rightCam;
}

void
AnimConfig::loadCameras(SoGroup* leftParent, SoGroup* rightParent)
{
	assert(leftParent);
	assert(rightParent);
	//SoWriteAction writeAction;
	//writeAction.apply(m_configSeparator);
	if (m_configSeparator) {
		// Load the camera and create the separated cameras.

		SoSearchAction mySearchAction;
		mySearchAction.setName("ViewCamera");
		mySearchAction.apply(m_configSeparator);
		if (mySearchAction.getPath() == NULL) // no left geometry found
		{
			cerr<<"Camera parameters not found in configuration file";
			exit(-1);
		}
		SoPath *p = new SoPath;
		p = mySearchAction.getPath();
		SoPerspectiveCamera* cam = (SoPerspectiveCamera*) p->getTail();
		
		mySearchAction.setName("CameraSeparation");
		mySearchAction.apply(m_configSeparator);
		if (mySearchAction.getPath() == NULL) 
		{
			cerr<<"Camera separation not found in configuration file";
			exit(-1);
		}
		p = mySearchAction.getPath();
		SoInfo* offsetInfo = (SoInfo*) p->getTail();
		float cameraOffset;
		istrstream offStr(offsetInfo->string.getValue().getString());
		offStr >> cameraOffset;

		SbRotation cameraRot = cam->orientation.getValue();
		SbVec3f leftPosition = SbVec3f(-cameraOffset, 0.0f, 0.0f);
		cameraRot.multVec(leftPosition, leftPosition);
		SbVec3f rightPosition = SbVec3f(cameraOffset, 0.0f, 0.0f);
		cameraRot.multVec(rightPosition, rightPosition);
		leftPosition += cam->position.getValue();
		rightPosition += cam->position.getValue();
		
		m_leftCam = new SoPerspectiveCamera;
		m_leftCam->heightAngle.setValue(cam->heightAngle.getValue());
		m_leftCam->viewportMapping.setValue(cam->viewportMapping.getValue());
		m_leftCam->position.setValue(leftPosition);
		//m_leftCam->position.setValue(0,0,5.5);
		m_leftCam->orientation.setValue(cameraRot);
		m_leftCam->aspectRatio.setValue(cam->aspectRatio.getValue());
		m_leftCam->nearDistance.setValue(cam->nearDistance.getValue());
		m_leftCam->farDistance.setValue(cam->farDistance.getValue());
		m_leftCam->focalDistance.setValue(cam->focalDistance.getValue());
		//m_leftCam->pointAt(SbVec3f(leftPosition[0],0,0));
		//m_leftCam->setStereoAdjustment(0.1);
		//m_leftCam->setStereoMode(SoCamera::StereoMode::LEFT_VIEW);
		
		m_rightCam = new SoPerspectiveCamera;
		m_rightCam->heightAngle.setValue(cam->heightAngle.getValue());
		m_rightCam->viewportMapping.setValue(cam->viewportMapping.getValue());
		m_rightCam->position.setValue(rightPosition);
		//m_rightCam->position.setValue(0,0,5.5);
		m_rightCam->orientation.setValue(cameraRot);
		//m_rightCam->pointAt(SbVec3f(rightPosition[0],0,0));
		m_rightCam->aspectRatio.setValue(cam->aspectRatio.getValue());
		m_rightCam->nearDistance.setValue(cam->nearDistance.getValue());
		m_rightCam->farDistance.setValue(cam->farDistance.getValue());
		m_rightCam->focalDistance.setValue(cam->focalDistance.getValue());
		//m_rightCam->setStereoAdjustment(0.1);
		//m_rightCam->setStereoMode(SoCamera::StereoMode::RIGHT_VIEW);


		leftParent->addChild(m_leftCam);
		rightParent->addChild(m_rightCam);
		
	
	} else {
		cerr << "AnimConfig ERROR: unable to load cameras." << endl;
	}
}

void
AnimConfig::loadGeometry(int* leftGeom, int* rightGeom)
{
	if (m_configSeparator)
	{
		SoSearchAction mySearchAction;

		/*
		// Look for Left Window Geometry
		mySearchAction.setName("LeftWindowGeometry");
		mySearchAction.apply(m_configSeparator);
		if (mySearchAction.getPath() == NULL) // no left geometry found
		{
			cerr<<"LeftWindowGeometry not found in configuration file";
			exit(-1);
		}
		else
		{
			SoPath *p = new SoPath;
			p = mySearchAction.getPath();
			SoInfo* leftInfo = (SoInfo*)p->getTail();
			istrstream inL(leftInfo->string.getValue().getString());
			if (leftGeom) {
			for (int i=0; i < 4; i++)
				inL >> leftGeom[i];
			}
		}

		mySearchAction.setName("RightWindowGeometry");
		mySearchAction.apply(m_configSeparator);
		if (mySearchAction.getPath() == NULL) // no left geometry found
		{	
			cerr<<"RightWindowGeometry not found in configuration file";
			exit(-1);
		}
		else
		{
			SoPath *p = new SoPath;
			p = mySearchAction.getPath();
			SoInfo* rightInfo = (SoInfo*)p->getTail();
			istrstream inR(rightInfo->string.getValue().getString());
			if (rightGeom) {
				for (int i=0; i < 4; i++)
					inR >> rightGeom[i];
			}
		}

		mySearchAction.setName("DisplayMode");
		mySearchAction.apply(m_configSeparator);
		if (mySearchAction.getPath() == NULL) // no left geometry found
		{	
			cerr<<"DisplayMode not found in configuration file"<<endl;
			cerr<<"Assuming BOTH windows to be displayed"<<endl;
			m_displayMode = "BOTH";
			//exit(-1);
		}
		else
		{
			SoPath *p = new SoPath;
			p = mySearchAction.getPath();
			SoInfo* modeInfo = (SoInfo*)p->getTail();
			m_displayMode = modeInfo->string.getValue().getString();
		}
		*/

		/*
		mySearchAction.setName("BindCenter");
		mySearchAction.apply(m_configSeparator);
		if (mySearchAction.getPath() == NULL) // no left geometry found
		{	
			cerr<<"BindCenter not found in configuration file"<<endl;
			cerr<<"Assuming BindCenter = ORIGIN " <<endl;
			m_bindCenter = "ORIGIN";
			//exit(-1);
		}
		else
		{
			SoPath *p = new SoPath;
			p = mySearchAction.getPath();
			SoInfo* bindCenterInfo = (SoInfo*)p->getTail();
			m_bindCenter = bindCenterInfo->string.getValue().getString();
		}
		*/
		/*
		mySearchAction.setName("FrameRate");
		mySearchAction.apply(m_configSeparator);
		if (mySearchAction.getPath() == NULL) // no left geometry found
		{	
			cerr<<"FrameRate not found"<<endl;
			cerr<<"Assuming FrameRate = NORMAL"<<endl;
			m_frameRate = "NORMAL";
			exit(-1);
		}
		else
		{
			SoPath *p = new SoPath;
			p = mySearchAction.getPath();
			SoInfo* frameRateInfo = (SoInfo*)p->getTail();
			m_frameRate = frameRateInfo->string.getValue().getString();
		}
		*/
		/*
		mySearchAction.setName("TextDisplay");
		mySearchAction.apply(m_configSeparator);
		if (mySearchAction.getPath() == NULL) // no left geometry found
		{	
			cerr<<"TextDisplay not found"<<endl;
			cerr<<"Assuming TextDisplay = ON"<<endl;
			m_textDisplay = "ON";
	//		exit(-1);
		}
		else
		{
			SoPath *p = new SoPath;
			p = mySearchAction.getPath();
			SoInfo* textDisplayInfo = (SoInfo*)p->getTail();
			m_textDisplay = textDisplayInfo->string.getValue().getString();
		}

		*/
	}
}

SoBlinker*
AnimConfig::getTextBlinker()
{
	return textBlinker;
}

/*
SoBlinker*
AnimConfig::loadFiles(const float& speed,const SbViewportRegion& region,SoSeparator *sceneFile)
{
//	CSearch *mySearch = new CSearch(m_config.getString());
	CSearch *mySearch = new CSearch(sceneFile);

	SoSeparator *files;
	files = mySearch->get("Data");
	if (files->getChild(0)->isOfType(SoInfo::getClassTypeId()))
	{
		SoInfo* pathToFiles =(SoInfo*) files->getChild(0);
		cout<<pathToFiles->string.getValue().getString();
		files = loadFileInDirectory(pathToFiles->string.getValue().getString());
	}

	//
	mySearch->get("BindCenter",m_bindCenter);
	mySearch->get("FrameRate",m_frameRate);
	mySearch->get( "TextDisplay",m_textDisplay);

	SbString modelName;
	if (files) {
		SoBlinker* animBlinker = new SoBlinker;
		textBlinker = new SoBlinker;
        
		cout<<"Number of children "<<files->getNumChildren()<<endl;
		for (int j=0; j<files->getNumChildren(); j++) {
			if (files->getChild(j)->isOfType(SoFile::getClassTypeId())) {
				SoFile* theFile = (SoFile*) files->getChild(j);

		//		theFile->ref

				cerr << "Loading " << theFile->name.getValue().getString() << endl;
				
				// Make 2D text here
				// Add each fileName into the textBlinker 
				modelName.makeEmpty();
				modelName = theFile->name.getValue().getString();

				// Adding 
				m_fileNames.push_back(modelName.getString());
				//

				SoSeparator *textSep = new SoSeparator;
				
				SoTranslation *textTrans = new SoTranslation;
				
				textTrans->translation.setValue(-1.0f,-0.8f,5.0f);
				SoText2 *modelText = new SoText2;
				modelText->string = modelName;
				
				
				textSep->addChild(textTrans);
				textSep->addChild(modelText);
				

				//bboxAction.apply(theGroup);

				SoTransform *animTransform = normalize(theFile, region);
				SoTransform * normalizeTrans = new SoTransform;
				normalizeTrans->translation.setValue(animTransform->translation.getValue());
	
				SoTransform * normalizeScale = new SoTransform;
				normalizeScale->scaleFactor.setValue(animTransform->scaleFactor.getValue());
	
				SoSeparator *aSep = new SoSeparator;
				//aSep->ref();
				if (m_bindCenter == "ORIGIN")
				{
					aSep->addChild(normalizeScale);
					aSep->addChild(normalizeTrans);
				}
				SoSeparator *cameraNuked = loadFile(theFile->name.getValue().getString(),1);
			//	aSep->addChild(theFile);
				aSep->addChild(cameraNuked);
				animBlinker->addChild(aSep);
				textBlinker->addChild(textSep);
//				theFile->unref();
			} else {
				cerr << "AnimConfig warning: found a non-File node.  "
					<< "Assuming the whole file should be added." << endl;
				
				// Make 2D text here
				// Add each fileName into the textBlinker 
				modelName.makeEmpty();
				modelName = m_config.getString();
				
				SoSeparator *textSep = new SoSeparator;
				
				SoTranslation *textTrans = new SoTranslation;
				textTrans->translation.setValue(-1.0f,-.8f,5.0f);
				SoText2 *modelText = new SoText2;
				modelText->string = modelName;
				
				// Adding 
				m_fileNames.push_back(modelName.getString());
				//
				
				textSep->addChild(textTrans);
				textSep->addChild(modelText);
				
				animBlinker->addChild(files);
				textBlinker->addChild(textSep);
				//animBlinker->whichChild.setValue(0);
				//animBlinker->on = TRUE;
				break;
			}

			
		}
		animBlinker->whichChild.setValue(0);
		animBlinker->on = TRUE;
		animBlinker->speed = speed;
		textBlinker->whichChild.setValue(0);
		textBlinker->on = TRUE;
		textBlinker->speed = speed;
		return animBlinker;
	} else {
		cerr << "AnimContrl ERROR: unable to load config file." << endl;
		return NULL;
	}

	files->unref();
	delete mySearch;
}
*/
SoTransform*
AnimConfig::normalize(SoNode* object,const SbViewportRegion& region)
{
	// Normalizing each object
	SoGetBoundingBoxAction bboxAction(region);
	bboxAction.apply(object);
	SbBox3f bbox = bboxAction.getBoundingBox();
	float xsize, ysize, zsize, scaleFactor;
	bbox.getSize(xsize, ysize, zsize);
	
	if (xsize > ysize)
		if (xsize > zsize)
			scaleFactor = xsize;
		else
			scaleFactor = zsize;
	else
		if (ysize > zsize)
			scaleFactor = ysize;
		else
			scaleFactor = zsize;
	scaleFactor = 1.0f / scaleFactor;
	SbVec3f rep;
	rep = bboxAction.getCenter();
	rep = -rep;
	SoTransform *animTransform = new SoTransform;
	//SoTranslation *animTranslate = new SoTranslation;
	animTransform->translation.setValue(rep);
	//SoScale *animScale = new SoScale;
	animTransform->scaleFactor.setValue(SbVec3f(scaleFactor,scaleFactor, scaleFactor));
	return animTransform;

}

SoTransform*
AnimConfig::scaleShapes(SoGroup* theGroup, const SbViewportRegion& region,
						SbBox3f& bbox, SbVec3f& rep)
{
	SoTransform* animTransform = new SoTransform;
	// Calculate the bounding box for the group.
	SoGetBoundingBoxAction bboxAction(region);
	
	bboxAction.apply(theGroup);
	bbox = bboxAction.getBoundingBox();
	
	float xsize, ysize, zsize, scaleFactor;
	bbox.getSize(xsize, ysize, zsize);
	
	if (xsize > ysize)
		if (xsize > zsize)
			scaleFactor = xsize;
		else
			scaleFactor = zsize;
		else
			if (ysize > zsize)
				scaleFactor = ysize;
			else
				scaleFactor = zsize;
			
			
			
			
#ifdef DEBUG
			cerr << "scaleFactor  = " << scaleFactor << endl;
#endif
			scaleFactor = 1.0f / scaleFactor;
#ifdef DEBUG
			cerr << "normalizing scaleFactor = " << scaleFactor << endl;
#endif
			
			
			
			
			rep = bboxAction.getCenter();
			
#ifdef DEBUG
			cerr << "center: " << rep[0] << " " << rep[1] << " " << rep[2] << endl;
#endif
			
			
			rep = -rep;
			animTransform->translation.setValue(rep);
			animTransform->scaleFactor.setValue(SbVec3f(scaleFactor,
				scaleFactor, scaleFactor));
			
#ifdef DEBUG
			cerr << "dimensions of bbox: " << xsize<< " " << ysize << " " << zsize << endl;
#endif
			
			return animTransform;
}

vector<string> AnimConfig::getFileNames()
{
	return m_fileNames;
}
