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
#ifndef WINDOW_H
#define WINDOW_H

#include "common.h"
#include "CSeismometer.h"
#include "CUtil.h"
#include "CText.h"
#include "CAnimConfig.h"
//#include "CAnimControl.h"
//#include "CSearch.h"
//#include "CText.h"
//#include "QUANTA.hxx"
#include <pthread.h>
#include "db.h"
#include "stock.h"
#include "brttpkt.h"
#include "brttutil.h"
#include "tr.h"
#include "Pkt.h"
#include "wv_connect_utils.h"

#define NUMCONSTS 9
#define PIx2 6.28318530718f

typedef void (*funcptr)( void );
//typedef void (*funcptr)( float );
/*
enum id_menu {	ID_NONE = 1,DEFAULTS1, DEFAULTS2, DEFAULTS3,
							DEFAULTS4, DEFAULTS5, DEFAULTS6,
							DEFAULTS7, DEFAULTS8, DEFAULTS9,
							ID_MONO, ID_AGAVE, ID_CROSSEYE,
							ID_QUIT};*/
enum id_menu { ID_NONE = 1, ID_QUIT};
//shalini for stereo
enum id_stereo { MONO=0, AGAVE, CROSSEYE };
enum STEREOVIEW { LEFT, RIGHT};

class CWindow
{
public:

	// Constructor/destructor
	CWindow( char *szWindowTitle, int height, int width,  int , int, Wv_datalink * );
	//CWindow( string szWindowTitle, string animFile, string configFile);
    ~CWindow( void );

	//
	// Variables - Window related
	//
    
//	bool init;				// flag tells if windows/glut wss intialize or not
    char lastError[256];	// Last error
	char lastCommand[256];	// Last command
	
    static int  w_width, w_height;
    static int  w_width_original, w_height_original;
	int  window_id;// current window id returned by GLUT create window
	int  menu_id;

	bool verbose;	// Flag to 'verbose' or show more debug detalis on console
	id_stereo stereoType; //flag to indicate the stereo type that is actively current

	// Scene related
	static SoSceneManager * scenemanager;
	static SoSeparator *sceneRoot;
	static SoSwitch *root;
	static SoDirectionalLight *frontLight, *topLight;
	static SoScale *sceneScale;
	static SoRotation *sceneRot;
	static SoTranslation *sceneTranslate;
	//static SoRotor *localRotor;
	static SoSeparator* theAnim;
	static SoBlinker *animBlinker;
	static AnimConfig* animConfig;
	static SoTransform* g_normalizeXform;
//	static AnimControl *animControl;
//	static CText *myText;
//	static AnimControl *animTextControl;
	static SoMaterial *textMaterial;
	static SoMaterial *sphereMaterial;
	static SoSelection *selectionRoot;
	static SoAnnotation *myAnnotation;
	static SoComplexity *sphereComplexity;
	static SoDrawStyle *sphereDrawStyle;
	static SoComplexity *animComplexity;
	static SoDrawStyle *animDrawStyle;
	
	static float reddish[3];
	static float white[3];

	static float ztrans;
	static float xtrans;
	static float ytrans;
	static SbVec2s g_zoomPos;
	static SbVec2f g_rotLoc;
	static SbVec2s g_panPos;

	// Flags
	static string g_displayMode;
	static SbBool g_textDisplay;
	static float g_sceneScaleFactor;
	static float g_rotationIncrement;
	static SbBool g_doRotY;
	static SbBool g_doZoom;
	static SbBool g_doRotate;
	static SbBool g_doPan;
	static SbBool fullscreen;
	static SbBool g_i_started_spin;
 	static int speedFactor;	


	// GLUT menu and keyboard tables
	funcptr eventKeyTable[256];
	funcptr eventKeyUpTable[256];
	struct
	{
		bool item_enable;
		char item_text[256];	
		funcptr item_function;// function to call
	} menuTable[256];
	

	// Euphoria local 
	// Parameters edited in the dialog box

	//
	// Functions - Window related
	//
	void mainLoop(  void* );
    void eventKey(  unsigned char key, funcptr ptr);
    void eventKeyUp(  unsigned char key, funcptr ptr);
    //void addMenu(   id_menu idNewItem, char *newLabel, funcptr );

	//
	// Euphoria related
	//
	//void setDefaults( int which );
	//void initSaver(   void );

    //
    // Static functions - Window related
    //    
	static void Draw(		    void );
	static void DrawOneEye( STEREOVIEW curView);
	static void UpdateDisplay(  void );
    static void ReShape( int width, int height );
	//static void keyboard( unsigned char key, int x, int y );
	//static void handleSpecialKeyboard( int key, int x, int y );
	//static void handleKeyRelease( unsigned char key, int x, int y);
	//static void menuWin( int value );
	static void processMouse(int button, int state, int x, int y);
	static void processMouseActiveMotion(int x, int y);
	static void Quit( void );
	
	static void mySelectionCB(void*, SoPath*);
	static void myDeselectionCB(void*,SoPath*);
	static void mouseZoomCB(void* userData, SoEventCallback* eventCB);

	static void redraw_cb(void * user, SoSceneManager * manager);
	static void expose_cb(void);
	static void idle_cb(void );
	static void drawScene(void);
	static void doRot(float angle, char axis);

	//static void Regular( void );
	//static void Grid(    void );
	//static void Cubism(  void );
	//static void BadMath( void );
	//static void MTheory( void );
	//static void UHFTEM(  void );
	//static void Nowhere( void );
	//static void Echo(    void );
	//static void Kaleidoscope( void );
	//for stereo shalini
	//static void AgaveStereo( void );
	//static void CrossEyedStereo( void );
	static void Mono( void );
	static void play( void );
	static void spinOnY( void );
	static void spin( void );
	static void toggleText( void );
	static void previous( void );
	static void next( void );

	static void fullScreen( void );
	static void zoomIn( void );
	static void zoomOut(  void );
	static void RotateX(  void );
	static void RotateY(  void );
	static void RotateZ(  void );
	static void CounterRotateX(  void );
	static void CounterRotateY(  void );
	static void CounterRotateZ(  void );
	static void PanUp(  void );
	static void PanDown( void );
	static void PanLeft( void );
	static void PanRight( void );
	static void PlaybackFaster( void );
	static void PlaybackSlower( void );
	static void AutoSpin( void );
	static void SpinFaster( void );
	static void SpinSlower( void );
	static void reset( void );
	static void popfifo( int);

//	static void * threadedFunction(void*);



/* 	static SoCoordinate3 *markerCoords; */
/* 	static CGlyph *velGlyph; */
/* 	static CData *nData; */
/* 	static CData *eData; */
/* 	static CData *zData; */

/* 	static SoCoordinate3 *nCoords; */
/* 	static SoCoordinate3 *eCoords; */
/* 	static SoCoordinate3 *zCoords; */
/* 	static SoCoordinate3 *bhnCoords; */
/* 	static SoCoordinate3 *bheCoords; */
/* 	static SoCoordinate3 *bhzCoords; */
/* 	static SoCoordinate3 *particleCoords; */
/* 	static SoCoordinate3 *headLineCoords; */
/* 	static SoTranslation *headTrans; */

/* 	static vector<float> nPts; */
/* 	static vector<float> ePts; */
/* 	static vector<float> zPts; */
       	static Pmtfifo *segments;
        static Wv_wfstruct *wvwf;
	
	static vector<CSeismometer*> network;
	static Wv_datalink *dl;
	static SbTime m_prevTime;
        static SbTime m_currTime;

	private:
		void init(string, string, string);
		static float m_numPtsMoved;
		static int m_numOfStations;
	//	SoMFVec3f npts;
		
};

#endif
