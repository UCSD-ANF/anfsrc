/******************************************************************
 * ImmersaView
 * Copyright (C) 2002 Electronic Visualization Laboratory,
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

#define WIGGLEVIEW_VERSION "0.1 - Dec 5, 2002"


#pragma warning(disable:4275)
#pragma warning(disable:4251)
#include <Inventor/SoDB.h>
#include <Inventor/SoInteraction.h>
#include <Inventor/SoPickedPoint.h>
#include <Inventor/actions/SoWriteAction.h>
#include <Inventor/engines/SoElapsedTime.h>
#include <Inventor/events/SoKeyboardEvent.h>
#include <Inventor/events/SoLocation2Event.h>
#include <Inventor/events/SoMouseButtonEvent.h>
#include <Inventor/manips/SoHandleBoxManip.h>
#include <Inventor/manips/SoTrackballManip.h>
#include <Inventor/manips/SoTransformerManip.h>
#include <Inventor/nodekits/SoCameraKit.h>
#include <Inventor/nodes/SoBlinker.h>
#include <Inventor/nodes/SoCone.h>
#include <Inventor/nodes/SoCube.h>
#include <Inventor/nodes/SoDirectionalLight.h>
#include <Inventor/nodes/SoEventCallback.h>
#include <Inventor/nodes/SoMaterial.h>
#include <Inventor/nodes/SoPerspectiveCamera.h>
#include <Inventor/nodes/SoRotationXYZ.h>
#include <Inventor/nodes/SoSelection.h>
#include <Inventor/nodes/SoSeparator.h>
#include <Inventor/nodes/SoSwitch.h>
#include <Inventor/nodes/SoTranslation.h>
#include <Inventor/nodes/SoText2.h>
#include <Inventor/nodes/SoFont.h>
#include <Inventor/nodes/SoDrawStyle.h>
#include <Inventor/nodes/SoRotor.h>
#include <Inventor/projectors/SbSphereSheetProjector.h>
//#include <Inventor/events/SoKeyboardEvent.h> 
#include <Inventor/actions/SoGLRenderAction.h>
#include <Inventor/engines/SoOneShot.h>


#ifdef _WIN32
#include <iostream>
#include <fstream>
using namespace std;
#else
#include <iostream.h>
#include <fstream.h>
#endif
#include "CAnimConfig.hxx"
#include "CAnimControl.hxx"
#include "CUtil.hxx"
#include "CSearch.hxx"
#include "CText.hxx"
#include "CSeismometer.hxx"
#include "CTimer.hxx"
#include "CSeismogram.hxx"
#include "QUANTA.hxx"
#include "CServer.hxx"

#define ACCESS_PORT 8003

int main(int, char**);
void showGraph(SoNode*);
void showUsage();


float ztrans = 0.0f;
float xtrans = 0.0f;
float ytrans = 0.0f;
SoTranslation *sceneTranslate=NULL;
AnimControl *animControl=NULL;
AnimControl *animTextControl=NULL;
SoAnnotation *myAnnotation=NULL;
SbVec2s g_zoomPos;
SbVec2f g_rotLoc;
SbVec2s g_panPos;
SbBool g_doZoom    = FALSE;
SbBool g_doRotate  = FALSE;
SbBool g_doPan     = FALSE;
SbBool g_doRotY = FALSE;
SbBool g_i_started_spin = FALSE;

string g_displayMode;
bool fullscreen = false;

SbBool g_textDisplay = TRUE;


SoSeparator* theAnim;
SoBlinker *animBlinker;
AnimConfig* animConfig;
SoTransform*  g_normalizeXform = NULL;
SoDirectionalLight *frontLight, *topLight;
SoScale *sceneScale = NULL;
SoRotor *localRotor = NULL;
SoRotation *sceneRot = NULL;
SoSwitch *root = NULL;
CText *myText;

int     g_viewW, g_viewH;
int     g_viewW_original, g_viewH_original;

float g_sceneScaleFactor = 1.0f;
float g_rotationIncrement = 1.0f;

const float SCALE_FACTOR        = 0.1f;
const float PAN_FACTOR          = 0.01f;
const float ROTATION_INCREMENT  = 2.0f;
const float AUTO_SPIN_INCREMENT = 0.01f;
const float AUTO_SPIN_MIN       = 0.02f;
const float ANIMATION_SPEED     = 0.1f;

#include <GL/glut.h>
SoSceneManager * scenemanager;


char g_serverAddress[1024];
int g_limRemotePort;

void toggleKeyAction(unsigned char,int );
void doRot(float , char );

char* configFile = NULL;

// wiggleview
vector<CSeismometer*> g_Seismometers;
vector<string> g_traceNames;
map<string, CSeismogram> g_Seismograms;
QUANTAts_mutex_c quantaMutex;
Server *mylink;
void* threadedFunction(void*);
void addChannelToSeismoMeters(CChannel * );
int g_numSeismosDisplayed;

float myTimer, g_updateRate;
SbBool g_startEvent = FALSE;
SbBool g_pauseEvent = FALSE;
//float g_eventStartTime;
double g_eventStartTime;
SoOneShot *eventControl;
enum DisplayOptions {
	BOTH = 0,
	ONLY_WIGGLES,
	ONLY_PARTICLE
};
DisplayOptions g_display;
SbBool g_drawOnGlobe = TRUE;

int numOfPtsAdded; // pass this to the Seismometers so that they know how many points
				   // to draw in the next update
float timeInMilliSecs;
float addToTimer;
void timerFunc(int);
float g_eventTrans[3];
float g_eventLatLong[2];
SoTranslation *eventTrans;
// ----------------------------------------------------------------------


void doRot(float angle, char axis)
{
	SbVec3f X;
	SbVec3f Y;
	SbVec3f Z;
	X.setValue(1,0,0);
	Y.setValue(0,1,0);
	Z.setValue(0,0,1);
	
	SbMatrix newRotMatrix;
	
	SbMatrix rotMatrix;
	SbRotation r = sceneRot->rotation.getValue();
	r.getValue(rotMatrix);
	
	SbRotation rX(X,angle*3.14/180);
	SbRotation rY(Y,angle*3.14/180);
	SbRotation rZ(Z,angle*3.14/180);
	
	switch(axis){
	case 'x':
		newRotMatrix.setRotate(rX);
		rotMatrix.multRight(newRotMatrix);
		break;
	case 'y':
		newRotMatrix.setRotate(rY);
		rotMatrix.multRight(newRotMatrix);
		break;
    case 'z':
		newRotMatrix.setRotate(rZ);
		rotMatrix.multRight(newRotMatrix);
		break;
	default:
		break;
	}
	
	sceneRot->rotation = rotMatrix;
}


void drawScene(void)
{
	SoGLRenderAction * myRenderAction;

	
	if (g_displayMode == "STEREO")
	{
		
		SbViewportRegion regionL, regionR;
		regionL.setViewportPixels(0, 0, g_viewW/2, g_viewH); //L, B, W, H
		regionR.setViewportPixels(g_viewW/2, 0, g_viewW/2, g_viewH);
		root->whichChild = 0;
		myRenderAction = new SoGLRenderAction(regionL);
		//myRenderAction->setTransparencyType(SoGLRenderAction::SORTED_OBJECT_ADD);
		myRenderAction->setTransparencyType(SoGLRenderAction::DELAYED_BLEND);

		//myText.normalize(regionL);
		// maybe need to do more GL here - turn off back face culling
		// check near and far buffers
	    glDisable(GL_CULL_FACE); 
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
		myRenderAction->apply(root);

		root->whichChild = 1;
		//myText.normalize(regionR);
		myRenderAction->setViewportRegion(regionR);
		myRenderAction->apply(root);
    }
	else
	{

		SbViewportRegion region;
		region.setViewportPixels(0, 0, g_viewW, g_viewH); //L, B, W, H
		myRenderAction = new SoGLRenderAction(region);
		//myRenderAction->setTransparencyType(SoGLRenderAction::SORTED_OBJECT_ADD);
		myRenderAction->setTransparencyType(SoGLRenderAction::DELAYED_BLEND);
	    	root->whichChild = 0;
        	glDisable(GL_CULL_FACE); 
        	glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
	    	myRenderAction->apply(root);
	}

		// Handle state data
		//netSendKeyPress('C');

}


// Redraw on scenegraph changes.
void
redraw_cb(void * user, SoSceneManager * manager)
{
	glEnable(GL_DEPTH_TEST);
	glEnable(GL_LIGHTING);
	drawScene();
	glutSwapBuffers();
}

// Redraw on expose events.
void
expose_cb(void)
{
	glEnable(GL_DEPTH_TEST);
	glEnable(GL_LIGHTING);
	drawScene();
	glutSwapBuffers();
	glutPostRedisplay();
}

// Reconfigure on changes to window dimensions.
void
reshape_cb(int w, int h)
{
	g_viewW = w;
	g_viewH = h;
	scenemanager->setWindowSize(SbVec2s(w, h));
	//scenemanager->setSize(SbVec2s(w, h));
	//scenemanager->setViewportRegion(SbViewportRegion(w, h));
	scenemanager->scheduleRedraw();
}

// Process the internal Coin queues when idle. Necessary to get the
// animation to work.
void
idle_cb(void)
{
	sceneTranslate->translation.setValue(xtrans, ytrans, ztrans);
	sceneScale->scaleFactor.setValue(g_sceneScaleFactor,g_sceneScaleFactor,g_sceneScaleFactor);

	if (g_doRotY)
	{
		doRot(g_rotationIncrement, 'y');
	}

	if (g_startEvent == TRUE && g_pauseEvent == FALSE)
		myTimer+= g_updateRate;

	int i;
//	for (i = 0 ; i < g_Seismometers.size(); i++)
//		g_Seismometers[i]->update(myTimer,g_drawOnGlobe);
	
	SbBool startAgain = FALSE;
	for (i = 0 ; i <g_Seismometers.size(); i++)
	{		
		if (!g_Seismometers[i]->isFinished())
			break;
		else
			startAgain = TRUE;
	}
	if (startAgain == TRUE)
	{
		myTimer = g_eventStartTime;
		for (int i = 0; i <g_Seismometers.size(); i++)
		{
			g_Seismometers[i]->start();
			g_Seismometers[i]->reset();
		}
		g_startEvent = TRUE;
		eventControl->trigger.setValue();
		cout<<" startagain true Event started "<<endl;
	}
	

	/*
	quantaMutex.lock();
	cout<<" Number of seismograms currently: " << g_Seismograms.size()<<endl;
	if (g_Seismograms.size() > g_numSeismosDisplayed) 
	{
		// start building seismometers
		for (int i = g_numSeismosDisplayed; i < g_Seismograms.size(); i++)
		{
			// do stuff
			string stationId, siteId, channelId;
			string traceName = g_traceNames[i];
			int pos = traceName.find(':',0);
			stationId = traceName.substr(0,pos);
			int pos1 = traceName.find(':', pos+1);
			siteId = traceName.substr(pos+1, pos1-pos-1);
			channelId = traceName.substr(pos1+1,traceName.length()-pos1);
			cout<<"Parsed traceName : StationId "<<stationId<<" SiteId : "<<siteId
				<<" ChannelId : "<<channelId<<endl;
			float latitude, longitude, sampling;
			//latitude = 0.0f;
			//longitude = 0.0f;
			sampling = 0.5f;
			vector<int> amplitude;
			CSeismogram aSeismogram = g_Seismograms[traceName];
			latitude = aSeismogram.getLatitude();
			longitude = aSeismogram.getLongitude();
			amplitude = aSeismogram.getAmplitudeValues();

			bool done=false;
			//quantaMutex.lock();
			for (int i = 0; i < g_Seismometers.size(); i++)
			{
				if  (g_Seismometers[i]->getStationName() == stationId)
				{
					g_Seismometers[i]->addDataToChannel(stationId, siteId, channelId,
							latitude, longitude, sampling, amplitude);
					done = true;
					break;
				}
			}
			
			if (!done)
			{
				
				CSeismometer *newSeismometer = new CSeismometer();
				newSeismometer->addDataToChannel(stationId, siteId, channelId,
					latitude, longitude, sampling, amplitude);
				g_Seismometers.push_back(newSeismometer);
				theAnim->addChild(newSeismometer->getSep());
				
			}
		
		}
		g_numSeismosDisplayed = g_Seismograms.size();		
		
	}
	// Update here .. really dunno what is happening..
	//myTimer+=g_updateRate;
	//for (int i = 0; i < g_Seismometers.size(); i++)
	//	g_Seismometers[i]->update(myTimer);

	quantaMutex.unlock();

	*/
	// Write out the scene
	
	SoDB::getSensorManager()->processTimerQueue();
	SoDB::getSensorManager()->processDelayQueue(TRUE);
}

void HandleSpecialKeyboard(int key,int x, int y)
{
   switch (key) {
   case GLUT_KEY_LEFT:
	   {
   			cout<<"Left key pressed"<<endl;		
			for (int i = 0 ; i < g_Seismometers.size(); i++)
				g_Seismometers[i]->stretchTimeAxis(-0.1);
	   }
	   break;
   case GLUT_KEY_RIGHT:
	   {
      		cout<<"Right key pressed"<<endl;
			for (int i = 0 ; i < g_Seismometers.size(); i++)
				g_Seismometers[i]->stretchTimeAxis(0.1);
	   }
	   break;
   case GLUT_KEY_DOWN:    
	   {
		for (int i = 0 ; i < g_Seismometers.size(); i++)
			g_Seismometers[i]->stretchAmplitudeAxis(0.5);
	   }
	   break;
   case GLUT_KEY_UP:
	   {
		for (int i = 0 ; i < g_Seismometers.size(); i++)
			g_Seismometers[i]->stretchAmplitudeAxis(2);
	   }
	   break;
   case GLUT_KEY_PAGE_DOWN:
	   
	   break;
   case GLUT_KEY_PAGE_UP:
//	   commander->moveForward();
//	   commander->update();
	   break;
   case GLUT_KEY_F2:
		if (frontLight->on.getValue())
			frontLight->on = FALSE;
		else
			frontLight->on = TRUE;
	   break;
	case GLUT_KEY_F1:
//	   mainSwitch->whichChild = 0;
	   break;
	case GLUT_KEY_F3:
		if (topLight->on.getValue())
			topLight->on = FALSE;
		else
			topLight->on = TRUE;		
		break;
	case GLUT_KEY_F4:
		{
		animControl->next();
		animTextControl->next();
		if (g_drawOnGlobe)
			g_drawOnGlobe = FALSE;
		else
			g_drawOnGlobe = TRUE;
		}
	   break;
	default:
	   	break;
   }
}

// The P,Y,Enter,<,> keys need to be handled only when the key
// is released, so that repeated keypresses do not confuse the
// program
void HandleKeyRelease(unsigned char key, int x, int y)
{
	// If in collaboration then send the key to the server
	// Don't send Escape key - or send may be useful to keep track of who 
	// is still connected

	switch (key)
	{
		// Toggle the animation
		case 'p':
		case 'P':
			//animControl->toggleAnimation();
			//animTextControl->toggleAnimation();
			if (g_startEvent == FALSE)
			{
				myTimer = g_eventStartTime;
				for (int i = 0; i <g_Seismometers.size(); i++)
					g_Seismometers[i]->start();
				g_startEvent = TRUE;
				eventControl->trigger.setValue();
				cout<<" Event started "<<endl;

			}
			else
			{
				if (g_pauseEvent == FALSE)
				{
					for (int i = 0; i <g_Seismometers.size(); i++)
						g_Seismometers[i]->stop();
					g_pauseEvent = TRUE;
					cout<<" Event playback paused "<<endl;
				}
				else
				{
					for (int i = 0; i <g_Seismometers.size(); i++)
						g_Seismometers[i]->start();
					g_pauseEvent = FALSE;
					cout<<" Event playback restarted "<<endl;
				}
			}
			break;
		// Toggle auto-spint along the 'Y' axis of the object
		case 'y':
		case 'Y':
			g_doRotY = FALSE;
			if (localRotor->on.getValue())
			{
				localRotor->on.setValue(false);
			}
			else
			{
				localRotor->on.setValue(true);
			}
			break;
		case 'T':
		case 't':
			myText->toggleDisplay();
			break;
		// Go to previous
		case '<':
		case ',':
			if (g_updateRate > 101)
			g_updateRate-=100;
			if (g_startEvent == TRUE)
			{
				for (int i = 0; i <g_Seismometers.size(); i++)
					g_Seismometers[i]->previous();
			}
			//animTextControl->previous();
			break;
		// Go to next
		case '>':
		case '.':
			if (g_startEvent == TRUE)
			{
				g_updateRate+=100;
				for (int i = 0; i <g_Seismometers.size(); i++)
					g_Seismometers[i]->next();
			}
			break;
		// Toggle auto-spin about the Y axis
		case 13:
			if (localRotor->on.getValue())
				localRotor->on.setValue(false);
			if (g_doRotY)
			{
				g_doRotY = FALSE;
				g_i_started_spin = FALSE;
			}
			else
			{
				g_doRotY = TRUE;
				g_i_started_spin = TRUE;
			}
			break;
		default :
			break;
	}
	animTextControl->switchTo(animControl->getCurrentChild());
}



void keyboard(unsigned char userkey, int x, int y)
{

	static const float rotInc = ROTATION_INCREMENT;
	//set appropriate flag
	switch(userkey)
	{
	case 27:
		exit(0);
		break;
	case 'r':
	case 'R':
		g_sceneScaleFactor = 1.0f;
		xtrans = 0.0f;
		ytrans = 0.0f;
		ztrans = 0.0f;
		g_doRotY = FALSE;
		g_drawOnGlobe = TRUE;
		sceneRot->rotation.setValue(0,0,0,1);
		localRotor->rotation.setValue(0,1,0,0);
		localRotor->on.setValue(false);
		animControl->reset();
		animTextControl->reset();

		cerr << "Resetting the position of the model " << endl;
		break;
	case 'i':
	case 'I':
		ytrans+=PAN_FACTOR;
		break;
	case 'j':
	case 'J':
		xtrans-=PAN_FACTOR;
		break;
	case 'k':
	case 'K':
		ytrans-=PAN_FACTOR;
		break;
	case 'l':
	case 'L':
		xtrans+=PAN_FACTOR;
		break;
	case 'a':
	case 'A':
		doRot(rotInc, 'y');
		break;
	case 's':
	case 'S':
		doRot(rotInc, 'x');
		break;
	case 'w':
	case 'W':
		doRot(-rotInc, 'x');
		break;
	case 'd':
	case 'D':
		doRot(-rotInc, 'y');
		break;
	case '+':
	case '=':
		if (g_startEvent == TRUE && g_pauseEvent == FALSE)
		{
			//myTimer+=g_updateRate;
			//myTimer += 10;
			addToTimer += 1;
			numOfPtsAdded+= 20;
		}
		break;
	case '-':
	case'_':
		if (g_startEvent == TRUE && g_pauseEvent == FALSE)
		{
			//myTimer-=g_updateRate;
			//myTimer -= 10;
			//timeInMilliSecs+= 50;
			addToTimer -= 1;
			numOfPtsAdded -= 20;
		}
		break;
	case 'u':
	case 'U':
		if (g_sceneScaleFactor > SCALE_FACTOR)	
			g_sceneScaleFactor -= SCALE_FACTOR;				
		break;
	case 'o':
	case 'O':
		g_sceneScaleFactor += SCALE_FACTOR;
		break;
	case 'f':
	case 'F':
		if (fullscreen)
			fullscreen = false;
		else 
			fullscreen = true;
		if (fullscreen)
			glutFullScreen();
		else
			glutReshapeWindow(g_viewW_original,g_viewH_original);
		
		break;
	case 'e':
	case 'E':
		doRot(-rotInc, 'z');
		break;
	case 'q':
	case 'Q':
		doRot(rotInc, 'z');
		break;
	case '[':
	case '{':
		if (g_rotationIncrement > AUTO_SPIN_MIN)
		{	
			g_rotationIncrement -= AUTO_SPIN_INCREMENT;
#ifdef DEBUG
			cout<<"Spin Speed "<<g_rotationIncrement<<endl;
#endif
		}
		if (localRotor->speed.getValue() > AUTO_SPIN_MIN)
		{	
			localRotor->speed.setValue(localRotor->speed.getValue() - AUTO_SPIN_INCREMENT);
#ifdef DEBUG
			cout<<"Spin Speed "<<localRotor->speed.getValue()<<endl;
#endif
		}
		break;
	case ']':
	case '}':
		g_rotationIncrement += AUTO_SPIN_INCREMENT;
#ifdef DEBUG
		cout<<"Spin Speed "<<g_rotationIncrement<<endl;
#endif
		//if (localRotor->speed.getValue() < 0.2)
		{
			localRotor->speed.setValue(localRotor->speed.getValue() + AUTO_SPIN_INCREMENT);
#ifdef DEBUG
			cout<<"Spin Speed "<<localRotor->speed.getValue()<<endl;
#endif
		}
		break;
	case '/':
	case '?':
		int i;
		if (g_display == BOTH)//toggle Wiggles
		{
			for ( i = 0; i < g_Seismometers.size(); i++)
				g_Seismometers[i]->toggleParticle();
			g_display = ONLY_WIGGLES;
		}
		else
		if (g_display == ONLY_WIGGLES )
		{
			for ( i = 0; i < g_Seismometers.size(); i++)
			{
				g_Seismometers[i]->toggleWiggles();
				g_Seismometers[i]->toggleParticle();
			}
			// toggle Wiggles
			// toggle Particle
			g_display = ONLY_PARTICLE;
		}
		else
		if (g_display == ONLY_PARTICLE)
		{
			// toggle Particle
			// toggle Wiggles
			for ( i = 0; i < g_Seismometers.size(); i++)
			{
				g_Seismometers[i]->toggleWiggles();
				//Seismometers[i]->toggleParticle();
			}
			g_display = BOTH;	
		}
		
		
		//if (g_Seismometers[0]->isVisibleParticle())
		//	cout<<"Particles visible"<<endl;
		break;
	case 'g':
	case 'G':
		{
		SoOutput out;
		out.openFile("theAnim.iv");
		SoWriteAction writeAction(&out);
		writeAction.apply(theAnim);
		}
		break;
	default:
		//commander->moveForward();
        //commander->update();
		break;
	}


}

// project x,y onto a hemi-sphere centered within width, height
void ptov(int x, int y, int width, int height, float v[3]){
	float d, a;	
	v[0] = (2.0*x - width) / width;
	v[1] = (height - 2.0*y) / height;
	d = sqrt(v[0]*v[0] + v[1]*v[1]);
	v[2] = cos((M_PI/2.0) * ((d < 1.0) ? d : 1.0));
	a = 1.0 / sqrt(v[0]*v[0] + v[1]*v[1] + v[2]*v[2]);
	v[0] *= a;
	v[1] *= a;
	v[2] *= a;
}

void processMouse(int button, int state, int x, int y) {


	if ((state == GLUT_DOWN)) {
		
		// rotate
		if (button == GLUT_LEFT_BUTTON) {
			g_rotLoc[0] = x;
			g_rotLoc[1] = y;
			g_doZoom = FALSE;
			g_doPan = FALSE;
			g_doRotate = TRUE;
		}
		// zoom
		else if (button == GLUT_MIDDLE_BUTTON) {
			g_zoomPos[0] = x;
			g_zoomPos[1] = y;
			g_doZoom = TRUE;
			g_doPan = FALSE;
			g_doRotate = FALSE;
						
		}
		// pan
		else if (button == GLUT_RIGHT_BUTTON){
			g_panPos[0] = x;
			g_panPos[1] = y;
			g_doPan = TRUE;
			g_doZoom = FALSE;
			g_doRotate = FALSE;
		}		
	}
}

void processMouseActiveMotion(int x, int y) {

	if (g_doRotate)
	{
		//SbVec2s pos(x,y);
		#ifdef DEBUG
			cout<<"Mouse button1 clicked at "<<g_rotLoc[0]<<" "<<g_rotLoc[1]<<endl;
		#endif
		SbVec2f pos(x,y);
		#ifdef DEBUG
			cout<<"Mouse now at "<<pos[0]<<" "<<pos[1]<<endl;
		#endif
		float curPos[3], lastPos[3], dx, dy, dz;		
		//ptov(abs(pos[0]- g_viewW), pos[1], g_viewW/2.0, g_viewH, curPos);		
		//ptov(abs(g_rotLoc[0]-g_viewW), g_rotLoc[1], g_viewW/2.0, g_viewH, lastPos);		
		ptov((int)pos[0],(int) pos[1],(int) g_viewW,(int) g_viewH, curPos);		
		ptov(g_rotLoc[0], g_rotLoc[1], g_viewW, g_viewH, lastPos);		
		dx = curPos[0] - lastPos[0];
		dy = curPos[1] - lastPos[1];
		dz = curPos[2] - lastPos[2];

		float angle, axis[3];
		angle = 90.0 * sqrt(dx*dx + dy*dy + dz*dz);
		angle = angle * 3.14/180;
		axis[0] = lastPos[1]*curPos[2] - lastPos[2]*curPos[1];
		axis[1] = lastPos[2]*curPos[0] - lastPos[0]*curPos[2];
		axis[2] = lastPos[0]*curPos[1] - lastPos[1]*curPos[0];
		SbRotation r(axis, angle);
		SbMatrix newRotMatrix;
		r.getValue(newRotMatrix);

		SbMatrix rotMatrix;
		SbRotation r1 = sceneRot->rotation.getValue();
		r1.getValue(rotMatrix);
		rotMatrix.multRight(newRotMatrix);
		sceneRot->rotation = rotMatrix;
		g_rotLoc = pos;

	}

	if (g_doPan)
	{
		SbVec2s pos(x,y);

		double diffx, diffy;
		diffx = fabs(g_panPos[0] - pos[0])/g_viewW;
		diffy = fabs(g_panPos[1] - pos[1])/g_viewH;
		if (g_panPos[0] < pos[0])
			xtrans+=diffx;
		if (g_panPos[0] > pos[0])
			xtrans-=diffx;
		if (g_panPos[1] < pos[1])
			ytrans-=diffy;
		if (g_panPos[1] > pos[1])
			ytrans+=diffy;

		g_panPos = pos;

		//idle_cb();
	}
	if (g_doZoom) 
	{
		SbVec2s pos(x,y);
		if (g_zoomPos[1] < pos[1]) 
		{
			// Zoom out.
			g_sceneScaleFactor += SCALE_FACTOR;
			//cerr << "Zooming out ztrans is " << ztrans << endl;
		} 
		else 
			if (g_zoomPos[1] > pos[1]) 
			{
				// Zoom in.
				if (g_sceneScaleFactor > SCALE_FACTOR)	
					g_sceneScaleFactor -= SCALE_FACTOR;
					//cerr << "Zooming in ztrans is " << ztrans<< endl;
			}
			g_zoomPos = pos;

	}
}



int main(int argc, char **argv)
{

	// Display short description about Immersaview
	// Include version number and copyright information
	printf("\n\n---------------------------------------------------\n");
	printf("ImmersaView (version %s)\n",WIGGLEVIEW_VERSION);
	printf("Copyright 2002, Electronic Visualization Laboratory\n");
	printf("---------------------------------------------------\n\n\n");

	// Initialize Coin3d
	SoDB::init();
	SoInteraction::init();

	// wrt
	// Initiailize QUANTA
	QUANTAinit();
	QUANTAts_thread_c quantaThread;
	g_numSeismosDisplayed = 0;

	myTimer = 0.0;
	//g_updateRate = 100.0f;
	//myTimer = 100;
	timeInMilliSecs = 10.0f;
	numOfPtsAdded = 1;
	addToTimer = timeInMilliSecs*0.001;

	// Parse through the command-line arguments.
	g_display = BOTH;
	// Check if a file was provided
	char* animFile = NULL;
	if (argc > 1)
		animFile = argv[1];
	else {
		showUsage();
		exit(1);
	}

	

	// Currently this works for windows and linux
	// User can run program as immersaview C:/models/*.iv
	// This is really useful when you have a large number of data files
#if (defined(WIN32) || defined(linux))
	string aFile(animFile);
	if (aFile.find_first_of("*") != -1)
	{
		strcpy(animFile,loadFileWithWildCardInPath(argv[1]).c_str());
	}
#endif

	// The configFile is usually the second argument
	// Default is StereoCameras.iv 
	// This may change when Immersaview becomes collaborative
	if (argc > 2)
		configFile = argv[2];
	else {
		configFile = "StereoCameras.iv";
	}


	// wrt 
	// Thread off the networking here
	//
	int port = 5010;
	int dataport = 5011;
	mylink = new Server(port,dataport);
//	int i;
    	//quantaThread.create(threadedFunction, (void *) i);

	// Scan the config file for required info
	CSearch *mySearch = new CSearch(configFile);
	int lg[2], rg[2];
	int *windowPos = new int[2];
	mySearch->get("WindowPosition", windowPos, 2);
	
	int *windowSize = new int[2];
	mySearch->get("WindowSize", windowSize, 2);
	g_viewW = windowSize[0];
	g_viewH = windowSize[1];
	
	//string displayMode;
	mySearch->get("DisplayMode", g_displayMode);

	// Set up the root nodes.
	SoSeparator *sceneRoot = new SoSeparator;
	sceneRoot->ref();
	SoSeparator* rightRoot = new SoSeparator;
	rightRoot->ref();
	SoSeparator* leftRoot = new SoSeparator;
	leftRoot->ref();

	// Load the animation files.
	cerr << "Configuring Animation Config..." << endl;
	//AnimConfig* animConfig = new AnimConfig(animFile, configFile);
	animConfig = new AnimConfig(animFile, configFile);
	
	cerr << "Loading the animation files..." << endl;
	//SoSeparator* theAnim = new SoSeparator;
	theAnim = new SoSeparator;
	theAnim->ref();

	// Set up the FLTK windows.
	//int lg[4], rg[4];
	animConfig->loadGeometry(lg, rg);

	// initialize scenemanager instance

    scenemanager = new SoSceneManager;
    scenemanager->setRenderCallback(redraw_cb, (void *) NULL);
	//scenemanager->setBackgroundColor(SbColor(0.0f, 0.0f, 0.0f));
	SbViewportRegion s;
	scenemanager->setViewportRegion(s);
	scenemanager->activate();
	scenemanager->setSceneGraph(root);

	glutInit(&argc, argv);

    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGBA | GLUT_DEPTH);

	if (g_displayMode == "MONO")
	{
		g_viewW_original = g_viewW;
		g_viewH_original = g_viewH;
  		//glutInitWindowSize(g_viewW, g_viewH);
		cerr<<"Drawing a single window"<<endl;
	}
	else
		if (g_displayMode == "STEREO")
		{
			g_viewW *= 2;
			g_viewW_original = g_viewW;
			g_viewH_original = g_viewH;
			//glutInitWindowSize(g_viewW*2, g_viewH);
		}
		else
			{
				cerr<<"DisplayMode : "
					//<<displayMode
					<<" cannot be recognized. Please check configFile "
					//<<configFile
					<<endl;
				exit(0);
			}
	glutInitWindowSize(g_viewW, g_viewH);
	//glutInitWindowSize(512, 512);

    SbString title("window ");
//    title += (char)(i + 0x30);
	//if (i == 0 )
	glutInitWindowPosition(windowPos[0],windowPos[1]);
	//glutInitWindowPosition(0,0);
	

	sceneTranslate = new SoTranslation;
	sceneTranslate->translation.setValue(xtrans, ytrans, ztrans);
	
	
	sceneScale = new SoScale;
	
	

	localRotor = new SoRotor;
	localRotor->rotation.setValue(0,1,0,0);
	localRotor->speed.setValue(0.1f);
	localRotor->on.setValue(false);

	sceneRot = new SoRotation;
	


	//SoBlinker* animBlinker = animConfig->loadFiles(ANIMATION_SPEED,scenemanager->getViewportRegion());
	animBlinker = animConfig->loadFiles(ANIMATION_SPEED,scenemanager->getViewportRegion());
	animBlinker->ref();
	SoBlinker* animTextBlinker = animConfig->getTextBlinker();
	
		
	SoTransform *transToCenter = new SoTransform;
		
	
	animControl = new AnimControl(animBlinker);
	//animTextControl = new AnimControl(animTextBlinker);
	//animControl->switchTo(0);
	animControl->stop();
	///animTextControl->stop();
	
	cerr << "Placing cameras..." << endl;
	animConfig->loadCameras(leftRoot, rightRoot);
	
	// Setting up the text to be displayed
	//myText.init(animConfig->getFileNames());
	string textFlag;
	mySearch->get("TextDisplay", textFlag);
	if (textFlag == "OFF")
		g_textDisplay = FALSE;
	myText = new CText(animConfig->getFileNames());
	myText->normalize(scenemanager->getViewportRegion());
	myText->setPosition(-1,-1,0);
	
	
	if (!g_textDisplay)
		myText->toggleDisplay();
		
	animTextControl = new AnimControl(myText->getBlinker());
	animTextControl->setSpeed(0.1f);
	animTextControl->stop();
	
	// Setting up the lights in the scene Added Aug 11
	//CSearch mySearch(configFile);
	frontLight = new SoDirectionalLight;
	frontLight->setName("frontLight");

	string lightStatus;
	float lightIntensity;
	float lightDirection[3];
	float lightColor[3];

	mySearch->get("frontLightStatus", lightStatus);
	if (lightStatus == "ON")
		frontLight->on = TRUE;
	else
		frontLight->on = FALSE;
	mySearch->get("frontLightIntensity", lightIntensity);
	frontLight->intensity = lightIntensity;
	mySearch->get("frontLightDirection", lightDirection);
	frontLight->direction.setValue(SbVec3f(lightDirection));
	mySearch->get("frontLightColor", lightColor);
	frontLight->color.setValue(SbVec3f(lightColor));


	topLight = new SoDirectionalLight;
	topLight->setName("topLight");
	mySearch->get("topLightStatus", lightStatus);
	if (lightStatus == "ON")
		topLight->on = TRUE;
	else
		topLight->on = FALSE;
	mySearch->get("topLightIntensity", lightIntensity);
	topLight->intensity = lightIntensity;
	mySearch->get("topLightDirection", lightDirection);
	topLight->direction.setValue(SbVec3f(lightDirection));
	mySearch->get("topLightColor", lightColor);
	topLight->color.setValue(SbVec3f(lightColor));


	// Event Details
	CSearch mySearchQuake(argv[3]);

	string eNameAndTimeStr;
	mySearchQuake.get("EventNameAndTime", eNameAndTimeStr);
	SoText2 *eNameAndTime = new SoText2;
	eNameAndTime->string = eNameAndTimeStr.c_str();
	SoTranslation *eNameAndTimeTrans = new SoTranslation();
	//eNameAndTimeTrans->translation.setValue(-0.5f,1.8f,5.0f);
	eNameAndTimeTrans->translation.setValue(-0.6f,1.2f,-0.5f);
	SoSeparator *eNameAndTimeSep = new SoSeparator;
	eNameAndTimeSep->addChild(eNameAndTimeTrans);
	eNameAndTimeSep->addChild(eNameAndTime);

	// Add legend under the event name and time
	float *legendMat = new float[3];
	mySearchQuake.get("NMaterial", legendMat);
	SoText2 *legendN = new SoText2;
	legendN->string = "BHN";
	SoMaterial *legendNMat = new SoMaterial;
	legendNMat->diffuseColor.setValue(legendMat[0], legendMat[1], legendMat[2]);
	SoTranslation *legendNTrans = new SoTranslation;
	//legendNTrans->translation.setValue(-0.5f, 1.6f, 5.0f);
	legendNTrans->translation.setValue(-0.5f, 1.0f, -0.5f);
	SoSeparator *legendNSep = new SoSeparator;
	legendNSep->addChild(legendNMat);
	legendNSep->addChild(legendNTrans);
	legendNSep->addChild(legendN);

	mySearchQuake.get("EMaterial", legendMat);
	SoText2 *legendE = new SoText2;
	legendE->string = "BHE";
	SoMaterial *legendEMat = new SoMaterial;
	legendEMat->diffuseColor.setValue(legendMat[0], legendMat[1], legendMat[2]);
	SoTranslation *legendETrans = new SoTranslation;
	//legendETrans->translation.setValue(0.0f, 1.6fp, 5.0f);
	legendETrans->translation.setValue(0.0f, 1.0f, -0.5f);
	SoSeparator *legendESep = new SoSeparator;
	legendESep->addChild(legendEMat);
	legendESep->addChild(legendETrans);
	legendESep->addChild(legendE);

	mySearchQuake.get("ZMaterial", legendMat);
	SoText2 *legendZ = new SoText2;
	legendZ->string = "BHZ";
	SoMaterial *legendZMat = new SoMaterial;
	legendZMat->diffuseColor.setValue(legendMat[0], legendMat[1], legendMat[2]);
	SoTranslation *legendZTrans = new SoTranslation;
	//legendZTrans->translation.setValue(0.5f, 1.6f, 5.0f);
	legendZTrans->translation.setValue(0.5f, 1.0f, -0.5f);
	SoSeparator *legendZSep = new SoSeparator;
	legendZSep->addChild(legendZMat);
	legendZSep->addChild(legendZTrans);
	legendZSep->addChild(legendZ);

//	g_ztrans = new SoTranslation;
//	g_ztrans->translation.setValue(0,0,ztrans);
	
	mySearchQuake.get("EventClockUpdate", g_updateRate);


	// Creating the font node
	SoFont *myFont = new SoFont;
//	myFont->name.setValue("Times-Roman");
//	myFont->size.setValue(45.0);
	
//	SoDrawStyle *d = new SoDrawStyle;
//	d->style.setValue(SoDrawStyle::LINES);
//	d->lineWidth.setValue(3);
//	d->linePattern.setValue(0xf0f0);	// solid
	
	sceneRoot->addChild(myFont);

	// wiggleView Wilber stuff
	sceneRoot->addChild(eNameAndTimeSep);
	sceneRoot->addChild(legendNSep);
	sceneRoot->addChild(legendESep);
	sceneRoot->addChild(legendZSep);

	sceneRoot->addChild(frontLight);
	sceneRoot->addChild(topLight);

	sceneRoot->addChild(myText->getAnnotation());
	sceneRoot->addChild(sceneScale);
	sceneRoot->addChild(sceneTranslate);
	sceneRoot->addChild(sceneRot);
	sceneRoot->addChild(localRotor);
	sceneRoot->addChild(theAnim);
	
	leftRoot->addChild(animConfig->getLeftCamera());
	leftRoot->addChild(sceneRoot);
	
	rightRoot->addChild(animConfig->getRightCamera());
	rightRoot->addChild(sceneRoot);
	
	root = new SoSwitch;
	root->ref();
	root->addChild(leftRoot);
	root->addChild(rightRoot);
	root->whichChild = 0;
	
	
	SbBox3f bbox;
	SbVec3f rep;
	g_normalizeXform = animConfig->scaleShapes(animBlinker,
		scenemanager->getViewportRegion(), bbox, rep);
	
	SoTransform * normalizeTrans = new SoTransform;
	normalizeTrans->translation.setValue(g_normalizeXform->translation.getValue());
	
	SoTransform * normalizeScale = new SoTransform;
	normalizeScale->scaleFactor.setValue(g_normalizeXform->scaleFactor.getValue());
		
	//theAnim->addChild(normalizeScale);
	theAnim->addChild(normalizeTrans);
	theAnim->addChild(animBlinker);
	
	// Add Seismograms here
	int numOfStations;
	string e;
	mySearchQuake.get("NumberOfMeters", numOfStations);
	//mySearch.get("Event", e);
	int i;
	for (i = 0; i < numOfStations; i++)
	{
		CSeismometer *station = new CSeismometer(argv[3], i+1,g_drawOnGlobe);
		g_Seismometers.push_back(station);
		theAnim->addChild(g_Seismometers[i]->getSep());
	}

	float eLat,eLong;
	mySearchQuake.get("EventLatitude", eLat);
	mySearchQuake.get("EventLongitude", eLong);
	SoSeparator *eventSep = new SoSeparator;
	SoMaterial *eventMat = new SoMaterial;
	//SoTranslation *eventTrans = new SoTranslation;
	eventTrans = new SoTranslation;
	eventMat->diffuseColor.setValue(1.0f, 20.0f/255.0f, 147.0f/255.0f);
	eventMat->emissiveColor.setValue(1.0f, 20.0f/255.0f, 147.0f/255.0f);
	eventMat->transparency.setValue(0.3f);
	//eventTrans->translation.setValue(eLong * 1000/360, 0 , -eLat * 1000/180);
	float sphereRadius = 1.1f;
	g_eventTrans[0] = sphereRadius * sin(DTOR(eLong))*sin(DTOR(90-eLat));
	g_eventTrans[1] = sphereRadius * cos(DTOR(90-eLong));
	g_eventTrans[2] = sphereRadius * cos(DTOR(eLong))*sin(DTOR(90-eLat));

	g_eventLatLong[0] = eLat;
	g_eventLatLong[1] = eLong;

	if(g_drawOnGlobe)
		eventTrans->translation.setValue(g_eventTrans[0], g_eventTrans[1], g_eventTrans[2]);
	else
		eventTrans->translation.setValue(-g_eventLatLong[1]*0.00278746, g_eventLatLong[0]*0.00278746, -0.05);
	
	eventControl = new SoOneShot;
	eventControl->duration = 5;
	//eventRingControl->flags = SoOneShot::HOLD_FINAL;
	//SoCylinder *eventRing = new SoCylinder;
	//eventRing->parts = SoCylinder::SIDES;
	//eventRing->height = 0.3;
	//eventRing->radius.connectFrom(&eventRingControl->timeOut);

	SoSphere *eventSphere = new SoSphere;
	eventSphere->radius.connectFrom(&eventControl->timeOut);

	string eDetail;
	mySearchQuake.get("EventName", eDetail);
	SoText2 *eventText = new SoText2;
	eventText->string = eDetail.c_str();

	SoScale *eventScale = new SoScale;
	eventScale->scaleFactor.setValue(0.05, 0.05, 0.05);

	eventSep->addChild(eventMat);
	eventSep->addChild(eventTrans);
	eventSep->addChild(eventScale);
	eventSep->addChild(eventSphere);
	eventSep->addChild(new SoSphere);
	eventSep->addChild(eventText);
	//eventSep->addChild(eventRing);
	theAnim->addChild(eventSep);

	float eHour, eMins, eSecs, eYear, eMonth, eDay;
	mySearchQuake.get("EventStartYear", eYear);
	//mySearchQuake.get("EventStartMonth", eMonth);
	mySearchQuake.get("EventStartDay", eDay);
	mySearchQuake.get("EventStartHour", eHour);
	mySearchQuake.get("EventStartMins", eMins);
	mySearchQuake.get("EventStartSecs", eSecs);

	//if (eYear <= 99)
	//	eYear = eYear - 50;
	//else
	//	eYear = eYear + 50 +1;
	//m_startTime = (year*365*24*60*60)+(day*24*60*60)+(hour*60*60)+(mins*60)+secs;
	//eYear = eYear - 1950;
	//g_eventStartTime = (eYear*365*24*60*60) + (eDay*24*60*60) 
	//				+ (eHour *60 *60) + (eMins*60) + eSecs;
	g_eventStartTime = (eHour *60 *60) + (eMins*60) + eSecs;


	
	// Initialize system for collaboration
	// Always do this regardless of whether you are running 
	// single user or multiuser

	// Open a socket to receive data
	// 

	

	
	
	int glutwin = glutCreateWindow(title.getString());
    glutDisplayFunc(expose_cb);
    glutReshapeFunc(reshape_cb);
	glutKeyboardFunc(keyboard);
	glutSpecialFunc(HandleSpecialKeyboard);
	glutKeyboardUpFunc(HandleKeyRelease);

	//adding here the mouse processing callbacks
	glutMouseFunc(processMouse);
	glutMotionFunc(processMouseActiveMotion);
	//glutPassiveMotionFunc(processMousePassiveMotion);
	//glutEntryFunc(processMouseEntry);

//	glutIdleFunc(idle_cb);
	int val;
	glutTimerFunc(10,timerFunc,val);


	glutMainLoop();

  // clean up Coin resource use
//	netEndCollaboration();
	root->unref();
    delete scenemanager;
	return 0;


//	cerr << "Immersaview shutting down..." << endl;
}




void
showUsage()
{
	cerr << "Usage:" << endl
		<< "immersaview \"animConfig.iv\" [stereoConfig.iv]" << endl;
}

void* threadedFunction(void* data)
{
	mylink->connect();
	while(1)
	{
		int num_points[1];
		int * intbuffer;
		int len;
		mylink->recv_ints(&len,1);
		char* str = new char[len];
		int num = mylink->recv_string(str,len,'\0');
		string traceName(str);
		float loc[2];
		mylink->recv_floats(loc,2);
		cout<<"Latitude is "<<loc[0]<<" Longitude is "<<loc[1]<<endl;
		mylink->recv_ints(num_points,1);
                intbuffer = new int[num_points[0]];
                mylink->recv_ints(intbuffer,num_points[0]);

		quantaMutex.lock();
                vector<int> newData;
		CSeismogram aSeismogram;
                if (g_Seismograms.count(traceName) == 1)
	        	aSeismogram = g_Seismograms[traceName];
		else
		{
			g_traceNames.push_back(traceName);
			//g_numSeismosDisplayed++;
		}
                //quantaMutex.unlock();
		//cout<<"Before starting push size of newData is "<<newData.size()<<endl;
		aSeismogram.addAmplitudeValues(intbuffer,num_points[0]);
		aSeismogram.setLatitude(loc[0]);
		aSeismogram.setLongitude(loc[1]);
		//cout<<"Trace "<<traceName<<" Size = "<<newData.size()<<endl;
		//Channels[traceName] = newData;
		g_Seismograms[traceName] = aSeismogram;
                quantaMutex.unlock();
		mylink->closeSocket();
                mylink->connect();
                delete intbuffer;		
	}
	return NULL;
}
/*
void addChannelToSeismoMeters(CChannel * someChannel)
{
	bool done=false;
	quantaMutex.lock();
	for (int i = 0; i < g_Seismometers.size(); i++)
	{
		if  (g_Seismometers[i]->getStationId() == someChannel->getStationId())
		{
			g_Seismometers[i]->addChannel(someChannel);
			done = true;
			break;
		}
	}
	if (!done)
	{
		CSeismometer newSeismometer;
		newSeismometer.addChannel(someChannel);
		g_Seismometers.push_back(&newSeismometer);
		theAnim->addChild(newSeismometer.getSep());
	}
	quantaMutex.unlock();
}
*/

void timerFunc(int val )
{
	sceneTranslate->translation.setValue(xtrans, ytrans, ztrans);
	sceneScale->scaleFactor.setValue(g_sceneScaleFactor,g_sceneScaleFactor,g_sceneScaleFactor);
	
	if(g_drawOnGlobe)
		eventTrans->translation.setValue(g_eventTrans[0], g_eventTrans[1], g_eventTrans[2]);
	else
		eventTrans->translation.setValue(-g_eventLatLong[1]*0.00278746, g_eventLatLong[0]*0.00278746, -0.05);

	if (g_doRotY)
	{
		doRot(g_rotationIncrement, 'y');
	}

	if (g_startEvent == TRUE && g_pauseEvent == FALSE)
	{
		//myTimer+= g_updateRate;
		//myTimer+= timeInMilliSecs * 0.001;
		//myTimer += 1;
		myTimer += addToTimer;
		if (addToTimer != timeInMilliSecs * 0.001)
			addToTimer = timeInMilliSecs * 0.001;
		numOfPtsAdded = 1;
	}
		

	int i;
	for (i = 0 ; i < g_Seismometers.size(); i++)
		g_Seismometers[i]->update(myTimer,g_drawOnGlobe, numOfPtsAdded);
	
	SbBool startAgain = FALSE;
	for (i = 0 ; i <g_Seismometers.size(); i++)
	{		
		if (!g_Seismometers[i]->isFinished())
			break;
		else
			startAgain = TRUE;
	}
	if (startAgain == TRUE)
	{
		myTimer = g_eventStartTime;
		for (int i = 0; i <g_Seismometers.size(); i++)
		{
			g_Seismometers[i]->start();
			g_Seismometers[i]->reset();
		}
		g_startEvent = TRUE;
		eventControl->trigger.setValue();
		cout<<" startagain true Event started "<<endl;
	}
	
	SoDB::getSensorManager()->processTimerQueue();
	SoDB::getSensorManager()->processDelayQueue(TRUE);

	cout<<"Current time is "<<myTimer<<endl;
	glutTimerFunc(timeInMilliSecs, timerFunc, val);
}