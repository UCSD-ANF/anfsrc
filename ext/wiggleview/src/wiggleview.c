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

#define WIGGLEVIEW_VERSION "0.3 - Jan 27, 2003 Antelope "


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
#include "CServer.hxx"

#include "QUANTA.hxx"

//---------------------------------------------
//Antelope includes

#include "Pkt.h"
#include "orb.h"
#include "forb.h"
#include "coords.h"
#include "stock.h"
#include "db.h"

// New data structures for use with Antelope
QUANTAts_mutex_c quantaMutex;
vector<CSeismometer*> g_Seismometers; // a list of seismometers
vector<string> g_traceNames;        // a list of traces network:station:channel
map<string, CSeismogram> g_Seismograms; // a map of tracenames and seismograms
int g_numSeismosDisplayed;
//---------------------------------------------
//
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
string g_quakeConfigFile;

Server *mylink;
void* threadedFunction(void*);
void addChannelToSeismoMeters(CChannel * );

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
SbBool g_drawOnGlobe = FALSE;

int numOfPtsAdded; // pass this to the Seismometers so that they know how many points
				   // to draw in the next update
float timeInMilliSecs;
float addToTimer;
void timerFunc(int);
float g_eventTrans[3];
float g_eventLatLong[2];
SoTranslation *eventTrans;
SoScale *eventScale;
SbBool quickPlay = FALSE;
// ----------------------------------------------------------------------
//Antelope variables

char        c;
int rcode;
char *in,
     *out;
int orbin,
    orbout;
char *match = 0,
     *reject = 0;
int nmatch;
double          pkttime = 0.0 ;
int             pktid;
int             nbytes;
char        srcname[STRSZ];
char           *packet = 0;
int             packetsz = 0;
Packet         *unstuffed = 0;
int ichan;
PktChannel  *achan;

//-----------------------------------------------------------------
//
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
		//cout<<" startagain true Event started "<<endl;
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
   			//cout<<"Left key pressed"<<endl;		
			for (int i = 0 ; i < g_Seismometers.size(); i++)
				g_Seismometers[i]->stretchTimeAxis(-0.1);
	   }
	   break;
   case GLUT_KEY_RIGHT:
	   {
      		//cout<<"Right key pressed"<<endl;
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
			{
			int mod = glutGetModifiers();
			if (mod == GLUT_ACTIVE_ALT)
			{
				quickPlay = TRUE;
			}
			if (g_startEvent == FALSE)
			{
				myTimer = g_eventStartTime;
				for (int i = 0; i <g_Seismometers.size(); i++)
					g_Seismometers[i]->start();
				g_startEvent = TRUE;
				eventControl->trigger.setValue();
				//cout<<" Event started "<<endl;

			}
			else
			{
				if (g_pauseEvent == FALSE)
				{
					for (int i = 0; i <g_Seismometers.size(); i++)
						g_Seismometers[i]->stop();
					g_pauseEvent = TRUE;
					//cout<<" Event playback paused "<<endl;
				}
				else
				{
					for (int i = 0; i <g_Seismometers.size(); i++)
						g_Seismometers[i]->start();
					g_pauseEvent = FALSE;
					//cout<<" Event playback restarted "<<endl;
				}
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
		g_drawOnGlobe = FALSE;
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
			//cout<<"Spin Speed "<<g_rotationIncrement<<endl;
#endif
		}
		if (localRotor->speed.getValue() > AUTO_SPIN_MIN)
		{	
			localRotor->speed.setValue(localRotor->speed.getValue() - AUTO_SPIN_INCREMENT);
#ifdef DEBUG
			//cout<<"Spin Speed "<<localRotor->speed.getValue()<<endl;
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
		diffx = (g_panPos[0] - pos[0])/g_viewW;
		diffy = (g_panPos[1] - pos[1])/g_viewH;
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
	printf("Wiggleview (version %s)\n",WIGGLEVIEW_VERSION);
	printf("Copyright 2002, Electronic Visualization Laboratory\n");
	printf("---------------------------------------------------\n\n\n");

	// Initialize Coin3d
	SoDB::init();
	SoInteraction::init();

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
	g_quakeConfigFile = "TurkeyConfig.iv";
	if (argc < 2)
	      showUsage();

	// Antelope - the second arg should be some ip 
	// e.g. bbarray.ucsd.edu
	in = argv[2];
	if ((orbin = orbopen (in, "r&")) < 0)
	    die (0, "Can't open input '%s'\n", in);

	nmatch = orbselect( orbin, "AZ_YAQ.*" );
//	nmatch = orbselect( orbin, "AZ.*" );
	printf( "Restricting to AZ_YAQ: %d matches\n", nmatch );

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
	if (argc > 3)
		configFile = argv[3];
	else {
		configFile = "StereoCameras.iv";
	}


	// wrt 
	// Thread off the networking here
	//
	int i;
    	quantaThread.create(threadedFunction, (void *) i);

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

	// Creating the font node
	SoFont *myFont = new SoFont;
//	myFont->name.setValue("Times-Roman");
//	myFont->size.setValue(45.0);
	
//	SoDrawStyle *d = new SoDrawStyle;
//	d->style.setValue(SoDrawStyle::LINES);
//	d->lineWidth.setValue(3);
//	d->linePattern.setValue(0xf0f0);	// solid
	
	sceneRoot->addChild(myFont);

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
		<< "wiggleview \"animConfig.iv\" \"bbarray.ucsd.edu\" [stereoConfig.iv]" << endl;
}

void* threadedFunction(void* data)
{
	for(;;) {
	rcode = orbreap (orbin,
		    &pktid, srcname, &pkttime, &packet, &nbytes, &packetsz);
	printf( "srcname %s\ttimestamp %s\n", srcname, strtime( pkttime )  ); 

	    switch (unstuffPkt (srcname, pkttime, packet, nbytes, &unstuffed)) {
	      case Pkt_wf:
//		printf( "Got a waveform-data packet with %d channels\n", unstuffed->nchannels );
		for( ichan=0; ichan<unstuffed->nchannels; ichan++ ) {
		    	achan = (PktChannel*) gettbl( unstuffed->channels, ichan );
//		    	printf( "Chan %d is %s %s %s with %d samples\n",
//				ichan, achan->net, achan->sta, achan->chan, achan->nsamp );
			
			string channel(achan->chan);
			string net(achan->net);
			//cout<<"Channel "<<channel<<endl;
			if (channel == "BHE" || channel == "BHN" || channel == "BHZ")
			{
				quantaMutex.lock();
				string station(achan->sta);
				string traceName = net + ":" + station +
			    	":" + channel;
				cout<<"Tracename created is "<<traceName<<endl;
				CSeismogram aSeismogram;
				if (g_Seismograms.count(traceName) == 1)
				{
			    		CSeismogram bSeismogram = g_Seismograms[traceName];
			    		aSeismogram.setAmplitudeValues( bSeismogram.getAmplitudeValues());
			    		aSeismogram.setLatitude(bSeismogram.getLatitude());
			    		aSeismogram.setLongitude(bSeismogram.getLongitude());
			    		aSeismogram.setFrequency(bSeismogram.getFrequency());
			    		aSeismogram.m_network = bSeismogram.m_network;
			    		aSeismogram.m_station = bSeismogram.m_station;
			    		aSeismogram.m_channel = bSeismogram.m_channel;
//					cout<<"aSeismogram bSesimogram Lat Lon"<<" "<<aSeismogram.getLatitude()<<" "<<aSeismogram.getLongitude()<<" "<<bSeismogram.getLatitude()<<" "<<bSeismogram.getLongitude()<<endl;
				}
				else
				{
			    		//cout<<"Debug::Push back traceName to g_traceNames"<<endl;
			   		 g_traceNames.push_back(traceName);
					Dbptr   db;
					double  lat, lon;
					//char    *dbname = "/home/atul/quakes/dbmaster/anza";
					char    *dbname = "/home/kent/projects/brtt_ssn/anza_system/azsm/dbmaster/anza";
					dbopen( dbname, "r", &db );
					db = dblookup( db, 0, "site", 0, 0 );
					db.record = dbfind( db, achan->sta, 0, 0 );
					if( db.record < 0 ) {
						die( 0, "Couldn't find %s\n", station.c_str() );
					}
					dbgetv( db, 0, "lat", &lat, "lon", &lon, 0 );
					cout<<"From db lat lon "<<lat<<" "<<lon<<endl;
					aSeismogram.setLatitude((float)lat);
					aSeismogram.setLongitude((float)lon);

					cout<<"aSeismogram Lat Lon"<<" "<<aSeismogram.getLatitude()<<" "<<aSeismogram.getLongitude()<<endl;
				}
				aSeismogram.m_network = net;
				aSeismogram.m_station = station;
				aSeismogram.m_channel = channel;
				aSeismogram.addAmplitudeValues(achan->data,achan->nsamp);
				aSeismogram.setFrequency(1/achan->samprate);
				aSeismogram.setHaveNewData(TRUE);
				g_Seismograms[traceName] = aSeismogram;
				quantaMutex.unlock();
			}
		}
		break;

	      case Pkt_db:
		break;

	      case Pkt_pf:
		break;

	      case Pkt_ch:
		break;

	      default:
		break;
	    }
	

    }

    if (orbclose (orbin)) {
	complain (1, "error closing read orb\n");
    }

	return NULL;
}

void timerFunc(int val )
{
	sceneTranslate->translation.setValue(xtrans, ytrans, ztrans);
	sceneScale->scaleFactor.setValue(g_sceneScaleFactor,g_sceneScaleFactor,g_sceneScaleFactor);

	if (g_doRotY)
	{
		doRot(g_rotationIncrement, 'y');
	}


	quantaMutex.lock();
//	cout<<" Number of seismograms currently: " << g_Seismograms.size()<<endl;

	// Check if we have more Seismograms to display
	if (g_Seismograms.size() > g_numSeismosDisplayed)
	{
	    // start building seismometers
	    for (int i = g_numSeismosDisplayed; i < g_Seismograms.size(); i++)
	    {
		string traceName = g_traceNames[i];
		CSeismogram aSeismogram = g_Seismograms[traceName];

		bool done= false;
		for (int i = 0; i < g_Seismometers.size(); i++)
		{
		    if  (g_Seismometers[i]->getStationName() == aSeismogram.m_station)
		    {
			g_Seismometers[i]->addDataToChannel(aSeismogram.m_station,
				"00",
				aSeismogram.m_channel, 
				aSeismogram.getLatitude(),
				aSeismogram.getLongitude(), 
				aSeismogram.getFrequency(),
				aSeismogram.getAmplitudeValues());
			done = true;
			break;
		    }
		}
		if (!done)
		{
		    CSeismometer *newSeismometer = new CSeismometer(g_quakeConfigFile);
		    newSeismometer->addDataToChannel(aSeismogram.m_station,
			    		"00",
			   		aSeismogram.m_channel,
				        aSeismogram.getLatitude(),
					aSeismogram.getLongitude(),
				        aSeismogram.getFrequency(),
					aSeismogram.getAmplitudeValues());
		    newSeismometer->setHaveNewData(FALSE);
		    g_Seismometers.push_back(newSeismometer);
		    theAnim->addChild(newSeismometer->getSep());
		}
	    }
	    g_numSeismosDisplayed = g_Seismograms.size();
	}
	else
	{
	    for (int i = 0; i < g_Seismograms.size(); i++)
	    {
		//string stationId, siteId, channelId;
		string traceName = g_traceNames[i];
		//int pos = traceName.find(':',0);
		//stationId = traceName.substr(0,pos);
		//int pos1 = traceName.find(':', pos+1);
		//siteId = traceName.substr(pos+1, pos1-pos-1);
		//channelId = traceName.substr(pos1+1,traceName.length()-pos1);

		float latitude, longitude, sampling;
		sampling = 0.05f;
		vector<int> amplitude;
		CSeismogram aSeismogram = g_Seismograms[traceName];
//		if (aSeismogram.haveNewData() == TRUE)
//		{
		    latitude = aSeismogram.getLatitude();
		    longitude = aSeismogram.getLongitude();
		    amplitude = aSeismogram.getAmplitudeValues();
		    for (int i = 0; i < g_Seismometers.size(); i++)
	            {
			if  (g_Seismometers[i]->getStationName() == aSeismogram.m_station)
			{
			    g_Seismometers[i]->addDataToChannel(aSeismogram.m_station, 
				    "00", 
				    aSeismogram.m_channel, 
				    latitude, 
				    longitude, 
				    aSeismogram.getFrequency(), 
				    amplitude);
			   // aSeismogram.setHaveNewData(FALSE);
			   // g_Seismograms[traceName] = aSeismogram;
			}
		    }
		//}
	    }
	}
	for (int j = 0; j < g_Seismometers.size(); j++)
	     g_Seismometers[j]->update(g_drawOnGlobe);
	quantaMutex.unlock();
	
	SoDB::getSensorManager()->processTimerQueue();
	SoDB::getSensorManager()->processDelayQueue(TRUE);

	//cout<<"Current time is "<<myTimer<<endl;
	glutTimerFunc(timeInMilliSecs, timerFunc, val);
}
