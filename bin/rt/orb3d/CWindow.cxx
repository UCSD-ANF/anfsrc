//#include "common.h" 
//#include "readtex.h"
#include "CWindow.h"
#include <sys/time.h>
extern CWindow *w;

SoSceneManager * CWindow::scenemanager = NULL;
SoSeparator *CWindow::sceneRoot = NULL;
SoSwitch *CWindow::root = NULL;
SoSelection *CWindow::selectionRoot = NULL;
SoDirectionalLight *CWindow::frontLight = NULL, *CWindow::topLight = NULL;
SoScale *CWindow::sceneScale = NULL;
SoRotation *CWindow::sceneRot = NULL;
SoTranslation *CWindow::sceneTranslate = NULL;
//SoRotor *CWindow::localRotor = NULL;
SoSeparator* CWindow::theAnim = NULL;
SoBlinker *CWindow::animBlinker = NULL;
AnimConfig* CWindow::animConfig = NULL;
SoTransform* CWindow::g_normalizeXform = NULL;
//AnimControl *CWindow::animControl = NULL;
//CText *CWindow::myText = NULL;
//AnimControl *CWindow::animTextControl = NULL;
SoMaterial *CWindow::textMaterial=NULL;
SoMaterial *CWindow::sphereMaterial=NULL;
SoAnnotation *CWindow::myAnnotation = NULL;
SoComplexity *CWindow::sphereComplexity = NULL;
SoDrawStyle *CWindow::sphereDrawStyle = NULL;
float CWindow::reddish[] = {1.0, 0.2, 0.2};
float CWindow::white[] = {0.8, 0.8, 0.8};

float CWindow::ztrans = 5.0f;
float CWindow::xtrans = 0.0f;
float CWindow::ytrans = 0.0f;
int CWindow::w_height=0.0f;
int CWindow::w_width=0.0f;
int  CWindow::w_width_original = 0.0f, CWindow::w_height_original=0.0f;

// Flags
	
string CWindow::g_displayMode;
SbBool CWindow::g_i_started_spin = FALSE;
SbBool CWindow::g_textDisplay = TRUE;
float CWindow::g_sceneScaleFactor = 1.0f;
float CWindow::g_rotationIncrement = 0.1f;
SbBool CWindow::g_doRotY = FALSE;
SbBool CWindow::g_doZoom = FALSE;
SbBool CWindow::g_doRotate = FALSE;
SbBool CWindow::g_doPan = FALSE;
SbBool CWindow::fullscreen = FALSE;
SbVec2s CWindow::g_zoomPos;
SbVec2f CWindow::g_rotLoc;
SbVec2s CWindow::g_panPos;
int CWindow::speedFactor = 1;
Wv_datalink* CWindow::dl = NULL;

// SoCoordinate3 *CWindow::markerCoords=NULL;
SoComplexity *CWindow::animComplexity = NULL;
SoDrawStyle *CWindow::animDrawStyle = NULL;
// CGlyph *CWindow::velGlyph = NULL;
// CData *CWindow::nData = NULL;
// CData *CWindow::eData = NULL;
// CData *CWindow::zData = NULL;
Pmtfifo *CWindow::segments = NULL;
Wv_wfstruct *CWindow::wvwf = NULL;
// SoCoordinate3 *CWindow::nCoords = NULL;
// SoCoordinate3 *CWindow::eCoords = NULL;
// SoCoordinate3 *CWindow::zCoords = NULL;
// SoCoordinate3 *CWindow::bhnCoords = NULL;
// SoCoordinate3 *CWindow::bheCoords = NULL;
// SoCoordinate3 *CWindow::bhzCoords = NULL;
// SoCoordinate3 *CWindow::particleCoords = NULL;
// SoCoordinate3 *CWindow::headLineCoords = NULL;
// SoTranslation *CWindow::headTrans = NULL;
// vector<float> CWindow::nPts;
// vector<float> CWindow::ePts;
// vector<float> CWindow::zPts;

vector<CSeismometer*> CWindow::network;
SbTime CWindow::m_prevTime;
SbTime CWindow::m_currTime;
float CWindow::m_numPtsMoved;
int CWindow::m_numOfStations;

double xUnit;

void
CWindow::idle_cb(void)
{
	SoDB::getSensorManager()->processTimerQueue();
  	SoDB::getSensorManager()->processDelayQueue(TRUE);

}

void
CWindow::expose_cb(void)
{
	glEnable(GL_DEPTH_TEST);
  	glEnable(GL_LIGHTING);
  	scenemanager->render();

  	glutSwapBuffers();

}
void
CWindow::mouseZoomCB(void* userData, SoEventCallback* eventCB)
{
  const SoEvent* event = eventCB->getEvent();
  if(SO_MOUSE_PRESS_EVENT(event,BUTTON1))
    {
      cout<<"Inside  mouseZoomCB"<<endl;
      SoMouseButtonEvent* mouseEvent = new SoMouseButtonEvent;
      mouseEvent->setButton(SoMouseButtonEvent::BUTTON1);
      mouseEvent->setState(SoButtonEvent::DOWN);
      mouseEvent->setTime(SbTime::getTimeOfDay());
      SoHandleEventAction *aHandle = new SoHandleEventAction(scenemanager->getViewportRegion());;
      aHandle->setEvent(mouseEvent);
      aHandle->apply(root);
      eventCB->setHandled();
    }
  //	cout<<"Left mouse button clicked"<<endl;
	
  //mouseEvent->setPosition(SbVec2s(x,y));
  //scenemanager->processEvent(mouseEvent);
	
  //scenemanager->setHandleEventAction(aHandle);
}

SoPath*
pickFilterCB(void* data, const SoPickedPoint* pick)
{
  // See which child of selection got picked
  SoPath *p = pick->getPath();
  int i;
  for (i = 0; i < p->getLength() - 1; i++) {
    SoNode *n = p->getNode(i);
    if (n->isOfType(SoSelection::getClassTypeId()))
      break;
  }
	
  // Copy 2 nodes from the path:
  // selection and the picked child
  return p->copy(i, 2);
}

CWindow::CWindow( char *szWindowTitle, int width, int height,
		  int startX, int startY, Wv_datalink *mydl )
{

  memset( (void *)eventKeyTable, 0, sizeof( eventKeyTable ));
  memset( (void *)eventKeyUpTable, 0, sizeof( eventKeyUpTable ));
  //memset( (void *)menuTable,     0, sizeof( menuTable     ));



  w_width = width;
  w_height= height;

  cout<<"Before searching"<<endl;
  CSearch *mySearch = new CSearch(mydl->stereocameras_filename);
  int *windowPos = new int[2];
  mySearch->get("WindowPosition", windowPos);
  int *windowSize = new int[2];
  mySearch->get("WindowSize", windowSize);
  w_width = windowSize[0];
  w_height = windowSize[1];
  mySearch->get("DisplayMode", g_displayMode);
  cout<<"DisplayMode "<<g_displayMode<<endl;
  // Setting up the lights in the scene Added Aug 11
  //CSearch mySearch(mydl->stereocameras_filename);
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
  //  delete mySearch;

  // Init GLUT library
  glutInitWindowPosition( windowPos[0] ,windowPos[1] );
  if (g_displayMode == "CLONE")
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGBA | GLUT_DEPTH | GLUT_STEREO);
  else
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGBA | GLUT_DEPTH);
  if (g_displayMode == "MONO")
    {
      w_width_original = w_width;
      w_height_original = w_height;
      //glutInitWindowSize(w_width, w_height);
      cerr<<"Drawing a single window"<<endl;
    }
  else
    if (g_displayMode == "STEREO")
      {
	w_width *= 2;
	w_width_original = w_width;
	w_height_original = w_height;
	//cout<<"Window size is "<<w_width <<" "<<w_height<<endl;
	//glutInitWindowSize(w_width*2, w_height);
      }
    else
      if (g_displayMode == "CLONE")
	{
	  w_width_original = w_width;
	  w_height_original = w_height;
	  cerr<<"Drawing a single window for clone mode stereo"<<endl;
	}
      else
	{
	  cerr<<"DisplayMode : "
	    //<<displayMode
	      <<" cannot be recognized. Please check configFile "
	    //<<mydl->stereocameras_filename
	      <<endl;
	  exit(0);
	}
  cout<<"Window size is "<<w_width <<" "<<w_height<<endl;
  glutInitWindowSize(w_width, w_height);
	
  // Init OpenGL
#ifdef linux
  glShadeModel(GL_SMOOTH); // some speed-ups
#endif	
  window_id = glutCreateWindow( szWindowTitle );
  //glutFullScreen();

  // Set up the root nodes.
  SoSeparator *sceneRoot = new SoSeparator;
  sceneRoot->ref();
  SoSeparator* rightRoot = new SoSeparator;
  rightRoot->ref();
  SoSeparator* leftRoot = new SoSeparator;
  leftRoot->ref();

  SoSeparator *stereoCamerasFile = loadFile(mydl->stereocameras_filename);
  animConfig = new AnimConfig(stereoCamerasFile);
  cerr << "Placing cameras..." << endl;
  animConfig->loadCameras(leftRoot, rightRoot);

  //root = new SoSeparator;
  //SoPerspectiveCamera *myCamera = new SoPerspectiveCamera;
  //root->addChild(myCamera);
  //root->addChild(new SoDirectionalLight);

  scenemanager = new SoSceneManager;
  //scenemanager->setRenderCallback(redraw_cb, (void *) NULL);
  //scenemanager->setBackgroundColor(SbColor(0.0f, 0.0f, 0.0f));
  SbViewportRegion s;
  //s.setViewportPixels(0, 0, w_width, w_height);
  scenemanager->setViewportRegion(s);
  scenemanager->activate();
  scenemanager->setSceneGraph(root);

	/* Getting parameters */
        Wv_datalink *dl = (Wv_datalink *) mydl;
        Wv_wfstruct *wvwf;
        Wv_stachaninfo *wvsci;
        int     rc;
        int     loop = 1;
        Tbl     *keys;
        int     ikey;
        char    *key;

        keys = keysarr( dl->display_channels );

        fprintf( stderr, "\n\nnographics_start: Initial display_channels setup information:\n" );

        for( ikey = 0; ikey < maxtbl( keys ); ikey++ ) {

                key = (char *) gettbl( keys, ikey );

                wvsci = (Wv_stachaninfo *) getarr( dl->display_channels, key );

                fprintf( stderr, "\nDisplaying station %s channel %s\n"
                                 "\tlat %f, lon %f, elev %f meters\n"
                                 "\ttimespan %f seconds, amplitude scale %f to %f\n",
                                wvsci->sta,
                                wvsci->chan,
                                wvsci->lat,
                                wvsci->lon,
                                wvsci->elev_meters,
                                wvsci->twin_sec,
                                wvsci->amplitude_min,
                                wvsci->amplitude_max );
	string sta(wvsci->sta);
	bool addStationFlag = true;
 	 if (network.size() > 0) {
		for (int i = 0; i < network.size(); i++)
			if (network[i]->getStationName() == sta) {
				cout<<"Station "<<sta<<" already exists"<<endl;
				addStationFlag = false;
				break;
			}
		
	}
	if (addStationFlag){ 
  		CSeismometer *aSeismometer = new CSeismometer(wvsci->sta, wvsci->lat, wvsci->lon, wvsci->elev_meters,wvsci->amplitude_min,wvsci->amplitude_max );
  		network.push_back(aSeismometer);
		m_numOfStations += 1;
		cout<<"No of stations in the network "<<m_numOfStations<<endl;
	}
     }


        /* */
  //cout<<"Before making new CSeismometer"<<endl;
  //CSeismometer *pfo = new CSeismometer("PFO", 0, 0);
  //cout<<"Before pushing into network vector"<<endl;
  //network.push_back(pfo);
	



	
  //	myCamera->viewAll(root, scenemanager->getViewportRegion(), 2.0);
  //SbVec3f pos(0,0,10);
  // Nov 25 , 2003
  // If I change the position of the camera to 0,0,-10 the camera
  // position does change but the glyp looks dark and the station name 
  // is inverted, so is the waveform annotation
  //myCamera->position = pos;
  //myCamera->pointAt(SbVec3f(0,0,0));
  //myCamera->nearDistance = 1;
  //myCamera->farDistance = 100;

  // Standard scene scale , translate, rotate and localrotor
  sceneTranslate = new SoTranslation;
  sceneTranslate->translation.setValue(xtrans, ytrans, ztrans);
		
  sceneScale = new SoScale;
/*	
  localRotor = new SoRotor;
  localRotor->rotation.setValue(0,1,0,0);
  localRotor->speed.setValue(0.1f);
  localRotor->on.setValue(false);
*/
  sceneRot = new SoRotation;
  sceneRot->rotation.setValue(SbVec3f(0,1,0), 3.14*3/4);
	
  animComplexity = new SoComplexity;

  animDrawStyle = new SoDrawStyle;
  animDrawStyle->style.setValue(SoDrawStyle::FILLED);

  sceneRoot->addChild(frontLight);
  sceneRoot->addChild(topLight);
  sceneRoot->addChild(sceneScale);
  sceneRoot->addChild(sceneTranslate);
  sceneRoot->addChild(sceneRot);
//  sceneRoot->addChild(localRotor);
  sceneRoot->addChild(animDrawStyle);
  sceneRoot->addChild(animComplexity);

  //velGlyph = new CGlyph(nData, eData, zData, numPts, true);
  //root->addChild(velGlyph->m_glyphSep);

  // Add tripod
  SoSeparator *tripod = loadFile(mydl->tripod_filename);
  sceneRoot->addChild(tripod);
  // Add grid
  SoSeparator *grid = loadFile(mydl->grid_filename);
  sceneRoot->addChild(grid);
  for (int i = 0; i < network.size(); i++)
    sceneRoot->addChild(network[i]->getSep());

  leftRoot->addChild(animConfig->getLeftCamera());
  leftRoot->addChild(sceneRoot);
	
  rightRoot->addChild(animConfig->getRightCamera());
  rightRoot->addChild(sceneRoot);
	
  root = new SoSwitch;
  root->ref();
  root->addChild(leftRoot);
  root->addChild(rightRoot);
  root->whichChild = 0;


  // root is now sceneRoot
  // Add a sphere node
  SoSeparator *sphereRoot = new SoSeparator;

  sphereDrawStyle = new SoDrawStyle;
  sphereDrawStyle->style = SoDrawStyle::FILLED;
  //sphereRoot->addChild(sphereDrawStyle);

  sphereComplexity = new SoComplexity;
  sphereComplexity->type = SoComplexity::OBJECT_SPACE;
  sphereRoot->addChild(sphereComplexity);

  SoTransform *sphereTransform = new SoTransform;
  //sphereTransform->translation.setValue(17.,17.,0.);
  //sphereTransform->scaleFactor.setValue(8.,8.,8.);
  //sphereRoot->addChild(sphereTransform);

  sphereMaterial = new SoMaterial;
  sphereMaterial->diffuseColor.setValue(.8,.8,.8);
  sphereRoot->addChild(sphereMaterial);
  sphereRoot->addChild(new SoSphere);
  //root->addChild(sphereRoot);

  SoSeparator *textRoot = new SoSeparator;
  SoTransform *textTransform = new SoTransform;
  textTransform->translation.setValue(0.,-1.,0.);
  textRoot->addChild(textTransform);

  textMaterial = new SoMaterial;
  textMaterial->diffuseColor.setValue(.8,.8,.8);
  textRoot->addChild(textMaterial);
  SoPickStyle *textPickStyle = new SoPickStyle;
  textPickStyle->style.setValue(SoPickStyle::BOUNDING_BOX);
  textRoot->addChild(textPickStyle);
  SoText2 *myText = new SoText2;
  myText->string = "rhubarb";
  textRoot->addChild(myText);
  //	root->addChild(textRoot);
  return;
}

CWindow::~CWindow( void )
{
  root->unref();
  delete scenemanager;
}

void CWindow::mySelectionCB(void *, SoPath* selectionPath)
{
  if (selectionPath->getTail()->
      isOfType(SoText2::getClassTypeId())) 
    {
      textMaterial->diffuseColor.setValue(reddish);
    }
  else if (selectionPath->getTail()->
	   isOfType(SoSphere::getClassTypeId()))
    {
      /*
	if (!myAnnotation)
	{
	myAnnotation = new SoAnnotation;
	myAnnotation->ref();
	}*/
      sphereMaterial->diffuseColor.setValue(reddish);
      SoSphere *aSphere = (SoSphere*)selectionPath->getTail();
      SoTransform *aTransform = new SoTransform;
      aTransform->translation.setValue(1.,30.,0.);
      aTransform->scaleFactor.setValue(1.,1.,1.);
      SoMaterial *aMaterial = new SoMaterial;
      aMaterial->diffuseColor.setValue(white);

      //myAnnotation->addChild(aTransform);
      //myAnnotation->addChild(aMaterial);
      //myAnnotation->addChild(aSphere);

      sphereComplexity->type = SoComplexity::BOUNDING_BOX;
      sphereDrawStyle->style = SoDrawStyle::LINES;

    }
  scenemanager->scheduleRedraw(); // Important to redraw

}

void CWindow::myDeselectionCB(void *, SoPath *deselectionPath)
{
  if (deselectionPath->getTail()->
      isOfType(SoText2::getClassTypeId())) {
    textMaterial->diffuseColor.setValue(white);
  }
  else if (deselectionPath->getTail()->
	   isOfType(SoSphere::getClassTypeId())){
    sphereMaterial->diffuseColor.setValue(white);
    //if (myAnnotation)
    //	myAnnotation->removeAllChildren(); // cool way of deleting all the children
    sphereComplexity->type = SoComplexity::OBJECT_SPACE;
    sphereDrawStyle->style = SoDrawStyle::FILLED;

  }
  scenemanager->scheduleRedraw();
}
/*
void CWindow::addMenu( id_menu idNewItem, char *newLabel, funcptr ptr_menuFunc)
{
  menuTable[idNewItem].item_enable   = true;
  menuTable[idNewItem].item_function = ptr_menuFunc;
  strcpy(menuTable[idNewItem].item_text, newLabel );
	
  if( glutGetMenu() == 0 )
    menu_id = glutCreateMenu( CWindow::menuWin );
	
  glutAddMenuEntry( newLabel, idNewItem );
}
*/
void CWindow::eventKey( unsigned char key, funcptr ptr_eventFunc )
{
  eventKeyTable[key] = ptr_eventFunc;
}

void CWindow::eventKeyUp( unsigned char key, funcptr ptr_eventFunc )
{
  eventKeyUpTable[key] = ptr_eventFunc;
}

void CWindow::popfifo(int val) 
{
	 Wv_wfstruct *wvwf;
        int     loop = 1;
        int     rc = 0;

	cout<<"Number of points that would be moved in dataPts"<<m_numPtsMoved<<endl;
        for (int i = 0; i < network.size(); i++)
                network[i]->scrollTimeAxis(m_numPtsMoved);
        m_numPtsMoved = 0;

        rc = pmtfifo_pop( dl->fifo, (void **) &wvwf );

        //        if( ( rc = pmtfifo_pop( dl->fifo, (void **) &wvwf ) ) == PMTFIFO_OK ) {
        if(  rc   == PMTFIFO_OK ) {
		fprintf( stderr, "\n\t\t\tgraphics_start: packet acquired!:\n" );
                        print_wv_wfstruct( stderr, wvwf );

//                        /* SCAFFOLD Atul fancy plotting */
	string channelId(wvwf->chan);
      string station(wvwf->sta);
      cout<<"Station is "<<station<<endl;
      cout<<"Channel is "<<channelId<<endl;
      int numPts = wvwf->pktchan->nsamp;
      float xUnit = wvwf->dt;
      float sampRate = wvwf->pktchan->samprate;
	 cout<<"Nsamp "<<numPts<<" xUnit "<<xUnit<<" sampRate "<<sampRate<<" time "<<wvwf->pktchan->time<<endl;
      vector<float> pts;
      for (int i = 0; i < numPts; i++)
        pts.push_back(wvwf->fdata[i]);
      for (int i = 0; i < network.size();i++)
        {
          if (network[i]->getStationName() == station)
            //network[i].addDataToChannel(channelId, numPts, xUnit, sampRate, pts);
		network[i]->addDataToChannel(channelId, numPts, xUnit, sampRate, pts, m_currTime.getValue(), wvwf->pktchan->time);
        }
                        free_wv_wfstruct( &wvwf );

                } else if( rc == PMTFIFO_NODATA ) {

                        fprintf( stderr, "\t\t\tgraphics_start: sleeping, no data \n" );

                        //sleep( 1 );

                } else if( rc == -1 ) {

                        clear_register( 1 );

                } else {

                        elog_complain( 1, "unrecognized pmtfifo result\n" );
                }
	

	glutTimerFunc(1000,popfifo, 1);

	



}
//
// Main loop
//

void CWindow::mainLoop( void * dlp )
{
	
	dl = (Wv_datalink *) dlp;
	m_prevTime.setToTimeOfDay();	

  //scenemanager->setRenderCallback(redraw_cb, dlp);
  // Before entering in the main loop, just add some callbacks
  //
  glutReshapeFunc( CWindow::ReShape);
  glutDisplayFunc( CWindow::UpdateDisplay );
  //glutDisplayFunc( CWindow::redraw_cb );
  //glutKeyboardFunc(CWindow::keyboard );
  //glutSpecialFunc(CWindow::handleSpecialKeyboard);
  //glutKeyboardUpFunc(CWindow::handleKeyRelease);
  glutIdleFunc(    CWindow::Draw );
  glutMouseFunc(CWindow::processMouse);
  glutMotionFunc(CWindow::processMouseActiveMotion);
	glutTimerFunc(1000,popfifo, 1);

  //glutAttachMenu(GLUT_RIGHT_BUTTON);
	CWindow::reset();	
	
  //glutIdleFunc(    CWindow::idle_cb );
  // Main event loop
  //
  glutMainLoop();
}

///////////////////////////////////////////////////////////////////
// Euphoria functions											 //
///////////////////////////////////////////////////////////////////
//

/*void CWindow::initSaver( void )//HWND hwnd)
  {


  }

  void CWindow::setDefaults(int which)
  {
	
  }
*/



void CWindow::Mono( void )
{
  //	w->stereoType = MONO;
}

void CWindow::play( void )
{
  cout<<" Toggling playback"<<endl;
  //seismograms->toggleAnimation();
  //velGlyph->toggleAnimation();	
  //	animControl->toggleAnimation();
  //	animTextControl->toggleAnimation();

}

void CWindow::spinOnY( void )
{
	
  g_doRotY = FALSE;
/*
  if (localRotor->on.getValue())
    {
      localRotor->on.setValue(false);
    }
  else
    {
      localRotor->on.setValue(true);
    }
*/	
}

void CWindow::spin( void )
{
	
  //	g_doRotY = FALSE;
/*  if (localRotor->on.getValue())
    localRotor->on.setValue(false);
*/ 
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
}

void CWindow::previous( void )
{
  //velGlyph->previous();
  //seismograms->previous();
  //	animControl->previous();
  //	animTextControl->switchTo(animControl->getCurrentChild());
}

void CWindow::next( void )
{
  //velGlyph->next();
  //seismograms->next();
  //	animControl->next();
  //	animTextControl->switchTo(animControl->getCurrentChild());
}

void CWindow::toggleText( void )
{
  //myText->toggleDisplay();
}

void CWindow::fullScreen( void )
{
  if (fullscreen)
    fullscreen = false;
  else 
    fullscreen = true;
  if (fullscreen)
    glutFullScreen();
  else
    //glutReshapeWindow(w_width_original,w_height_original);
    glutReshapeWindow(w_width,w_height);

}

void CWindow::zoomIn(void)
{
  if (g_sceneScaleFactor > IV_SCALE_FACTOR)	
    g_sceneScaleFactor -= IV_SCALE_FACTOR;
}

void CWindow::zoomOut( void )
{
  g_sceneScaleFactor += IV_SCALE_FACTOR;
}

void CWindow::RotateX( void)
{
  doRot(IV_ROTATE_FACTOR, 'x');
}

void CWindow::RotateY( void)
{
  doRot(IV_ROTATE_FACTOR, 'y');
}

void CWindow::RotateZ( void)
{
  doRot(IV_ROTATE_FACTOR, 'z');
}

void CWindow::CounterRotateX( void)
{
  doRot(-IV_ROTATE_FACTOR, 'x');
}

void CWindow::CounterRotateY( void)
{
  doRot(-IV_ROTATE_FACTOR, 'y');
}

void CWindow::CounterRotateZ( void)
{
  doRot(-IV_ROTATE_FACTOR, 'z');
}

void CWindow::PlaybackFaster( void)
{
  speedFactor++;
  //	animControl->animateFaster();
  //	animTextControl->animateFaster();
}

void CWindow::PlaybackSlower( void)
{
  if (speedFactor > 1)
    speedFactor--;
  //	animControl->animateSlower();
  //	animTextControl->animateSlower();
}


void CWindow::AutoSpin(void)
{
}

void CWindow::reset( void )
{
  //g_sceneScaleFactor = 1.0f;
  g_sceneScaleFactor = 3.0f;
  xtrans = 0.0f;
  ytrans = 0.0f;
  ztrans = 0.0f;
  g_doRotY = FALSE;
  g_i_started_spin = FALSE;
  //sceneRot->rotation.setValue(0,0,0,1);
  sceneRot->rotation.setValue(SbVec3f(0,1,0), 3.14 * 3/4);
  //sceneRot->rotation.setValue(SbVec3f(0.5,0.5,0.5), 3.14 + (3.14/4));
  //sceneRot->rotation.setValue(0.00391987,-1.50559e-05,0.000183993, 0.00616103);
  //localRotor->rotation.setValue(0,1,0,0);
  //localRotor->on.setValue(false);
  //velGlyph->stop();
  //velGlyph->reset();
  //seismograms->stop();
  //seismograms->reset();
  //	animControl->reset();
  //	animTextControl->reset();
  cerr << "Resetting the position of the model " << endl;

}

void CWindow::SpinFaster( void )
{
  g_rotationIncrement += IV_SPIN_FACTOR;
#ifdef DEBUG
  cout<<"Spin Speed "<<g_rotationIncrement<<endl;
#endif
	/*
    localRotor->speed.setValue(localRotor->speed.getValue() + IV_SPIN_FACTOR);
#ifdef DEBUG
    cout<<"Spin Speed "<<localRotor->speed.getValue()<<endl;
#endif
	*/
}

void CWindow::SpinSlower( void )
{
  if (g_rotationIncrement > AUTO_SPIN_MIN)
    {	
      g_rotationIncrement -= IV_SPIN_FACTOR;
#ifdef DEBUG
      cout<<"Spin Speed "<<g_rotationIncrement<<endl;
#endif
    }
	/*
  if (localRotor->speed.getValue() > AUTO_SPIN_MIN)
    {	
      localRotor->speed.setValue(localRotor->speed.getValue() - IV_SPIN_FACTOR);
#ifdef DEBUG
      cout<<"Spin Speed "<<localRotor->speed.getValue()<<endl;
#endif
    }
	*/
}

void CWindow::PanLeft( void )
{
  xtrans-=IV_PAN_FACTOR;
  float sendX = xtrans;
  float sendY = ytrans;
  float sendZ = ztrans;
}

void CWindow::PanRight( void )
{
  xtrans+=IV_PAN_FACTOR;
  float sendX = xtrans;
  float sendY = ytrans;
  float sendZ = ztrans;
}

void CWindow::PanDown( void )
{
  ytrans-=IV_PAN_FACTOR;
  float sendX = xtrans;
  float sendY = ytrans;
  float sendZ = ztrans;
}

void CWindow::PanUp( void )
{
  ytrans+=IV_PAN_FACTOR;
  float sendX = xtrans;
  float sendY = ytrans;
  float sendZ = ztrans;
}


//////////////////////////////////////////////////////////////////
// Static Windows functions										//
//////////////////////////////////////////////////////////////////

void CWindow::UpdateDisplay( void )
{
  glEnable(GL_DEPTH_TEST);
  glEnable(GL_LIGHTING);
  //sceneTranslate->translation.setValue(xtrans, ytrans, ztrans);
  //sceneScale->scaleFactor.setValue(g_sceneScaleFactor,g_sceneScaleFactor,g_sceneScaleFactor);
  //if (g_doRotY && g_i_started_spin)
  //	doRot(g_rotationIncrement, 'y');
  //drawScene();
  scenemanager->render();
  glutSwapBuffers();
  glutPostRedisplay();
	
  //int status = g_dbClient->process();
	
}
/*
void CWindow::keyboard( unsigned char key, int x, int y )
{ 

  if( w->eventKeyTable[key] != NULL )
    (w->eventKeyTable[key])();
	
}

void CWindow::handleSpecialKeyboard( int key, int x, int y)
{
  cout<<"Key value is "<<key<<endl;
  if( w->eventKeyTable[key] != NULL )
    (w->eventKeyTable[key])();
}

void CWindow::handleKeyRelease( unsigned char key, int x, int y)
{
  if( w->eventKeyUpTable[key] != NULL )
    (w->eventKeyUpTable[key])();
}

void CWindow::menuWin( int item_id)
{
  if( w->menuTable[item_id].item_enable )
    {
      strcpy( w->lastCommand, w->menuTable[item_id].item_text );
      (w->menuTable[item_id].item_function)();
      glutPostRedisplay();
    }
  //	GLUT_ACTIVE_CTRL = 0;
  //		glutDetachMenu(GLUT_RIGHT_BUTTON);

}
*/

void CWindow::processMouse(int button, int state, int x, int y) {

  //quantaMutex.lock();
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
      //int mod = glutGetModifiers();
      //if (mod == GLUT_ACTIVE_CTRL)
      //	glutAttachMenu(GLUT_RIGHT_BUTTON);
      //else
      //{
      //	glutDetachMenu(GLUT_RIGHT_BUTTON);
      g_panPos[0] = x;
      g_panPos[1] = y;
      g_doPan = TRUE;
      g_doZoom = FALSE;
      g_doRotate = FALSE;
      //}
    }		
  }
  else
    {
      animComplexity->type = SoComplexity::OBJECT_SPACE;
      animDrawStyle->style = SoDrawStyle::FILLED;
    }
  glutPostRedisplay();
  //quantaMutex.unlock();
}

void CWindow::processMouseActiveMotion(int x, int y) {

  //quantaMutex.lock();
  //	if (g_frameRate == "FAST")
  //	{
  //		animComplexity->type = SoComplexity::BOUNDING_BOX;
  //		animDrawStyle->style = SoDrawStyle::LINES;
  //	}
  glutSetCursor( GLUT_CURSOR_INFO );	
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
      //ptov(abs(pos[0]- w_width), pos[1], w_width/2.0, w_height, curPos);		
      //ptov(abs(g_rotLoc[0]-w_width), g_rotLoc[1], w_width/2.0, w_height, lastPos);		
      ptov((int)pos[0],(int) pos[1],(int) w_width,(int) w_height, curPos);		
      ptov(g_rotLoc[0], g_rotLoc[1], w_width, w_height, lastPos);		
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
      //cout<<"Angle now is "<<angle<<" Axis is "<<axis[0]<<" "<<axis[1]<<" "<<axis[2]<<endl;
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
      diffx = fabs((float)g_panPos[0] - pos[0])/w_width;
      diffy = fabs((float)g_panPos[1] - pos[1])/w_height;
      if (g_panPos[0] < pos[0])
	xtrans+=diffx;
      if (g_panPos[0] > pos[0])
	xtrans-=diffx;
      if (g_panPos[1] < pos[1])
	ytrans-=diffy;
      if (g_panPos[1] > pos[1])
	ytrans+=diffy;

      /*
	if (g_panPos[0] < pos[0])
	xtrans-=0.05f;
	if (g_panPos[0] > pos[0])
	xtrans+=0.05f;
	if (g_panPos[1] < pos[1])
	ytrans-=0.05f;
	if (g_panPos[1] > pos[1])
	ytrans+=0.05f;
      */
      g_panPos = pos;

      //		idle_cb();
      //sceneTranslate->translation.setValue(xtrans, ytrans, ztrans);	
      //glEnable(GL_DEPTH_TEST);
      //glEnable(GL_LIGHTING);
      //drawScene();
      //glutSwapBuffers();
    }
  if (g_doZoom) 
    {
      SbVec2s pos(x,y);
      if (g_zoomPos[1] < pos[1]) 
	{
	  // Zoom out.
	  g_sceneScaleFactor += IV_SCALE_FACTOR;
	  //cerr << "Zooming out ztrans is " << ztrans << endl;
	} 
      else 
	if (g_zoomPos[1] > pos[1]) 
	  {
	    // Zoom in.
	    if (g_sceneScaleFactor > IV_SCALE_FACTOR)	
	      g_sceneScaleFactor -= IV_SCALE_FACTOR;
	    //cerr << "Zooming in ztrans is " << ztrans<< endl;
	  }
      g_zoomPos = pos;

    }
  glutPostRedisplay();
	
  //quantaMutex.unlock();
}

void CWindow::ReShape( int width, int height )
{
  w_width = width;
  w_height = height;
  scenemanager->setWindowSize(SbVec2s(width, height));
  scenemanager->setSize(SbVec2s(width, height));
  scenemanager->setViewportRegion(SbViewportRegion(width, height));
  scenemanager->scheduleRedraw();
	
}

// Redraw on scenegraph changes.
void CWindow::redraw_cb(void * dlp, SoSceneManager * manager)
{

	Wv_datalink *dl = (Wv_datalink *) dlp;
        Wv_wfstruct *wvwf;
        int     loop = 1;
        int     rc = 0;

	cout<<"CWindow::redraw_cb"<<endl;
	
       // while( loop ) {


		rc = pmtfifo_pop( dl->fifo, (void **) &wvwf );

        //        if( ( rc = pmtfifo_pop( dl->fifo, (void **) &wvwf ) ) == PMTFIFO_OK ) {
                if(  rc   == PMTFIFO_OK ) {

                        fprintf( stderr, "\n\t\t\tgraphics_start: packet acquired!:\n" );

                        print_wv_wfstruct( stderr, wvwf );

//                        /* SCAFFOLD Atul fancy plotting */

                        free_wv_wfstruct( &wvwf );

                } else if( rc == PMTFIFO_NODATA ) {

                        fprintf( stderr, "\t\t\tgraphics_start: sleeping, no data \n" );

                        sleep( 1 );

                } else if( rc == -1 ) {

                        clear_register( 1 );

                } else {

                        elog_complain( 1, "unrecognized pmtfifo result\n" );
                }
        //}

  glEnable(GL_DEPTH_TEST);
  glEnable(GL_LIGHTING);
  //drawScene();
  scenemanager->render();
  glutSwapBuffers();
}


void CWindow::drawScene(void)
{
  SoGLRenderAction * myRenderAction;
  SbViewportRegion region;
  region.setViewportPixels(0, 0, w_width, w_height); //L, B, W, H
  myRenderAction = new SoGLRenderAction(region);
  //myRenderAction->setTransparencyType(SoGLRenderAction::SORTED_OBJECT_ADD);
  myRenderAction->setTransparencyType(SoGLRenderAction::DELAYED_ADD);
  //root->whichChild = 0;
  glDisable(GL_CULL_FACE); 
  glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
  myRenderAction->apply(root);
  delete myRenderAction;


}

void CWindow::Quit( void )
{
  exit(0);
}


///////////////////////////////////////////////////////////////////
// Static Euphoria functions									 //
///////////////////////////////////////////////////////////////////
//

#ifndef WIN32

static double timeGetTime()
{
  const double oneMicroSec = 0.000001;
  double seconds;
  struct timeval timeSec;
  struct timezone tzone;
	
  if( gettimeofday(&timeSec, &tzone) == -1 )
    {
      cerr << endl << "gettimeofday() error!";
      return( 0 );
    }
	
  seconds = (((double) timeSec.tv_sec) + (((double) timeSec.tv_usec) * oneMicroSec));
	
  printf("Seconds: %lf" , seconds);
	
  return( seconds * 1000.0  );
}

#endif

//the draw function to draw 2 stereo views
void CWindow::Draw(void) {

/*

*/
	m_currTime.setToTimeOfDay();
        SbTime diff;
        diff = m_currTime - m_prevTime;
        //cout<<"Time elapsed since last measurement"<<diff.getMsecValue()<<" ms"<<endl;
        //cout<<"No of points moved in dataPts "<<diff.getValue()*0.25<<endl;
        m_numPtsMoved += diff.getValue()*0.25;
        m_prevTime = m_currTime;
        for (int i = 0; i < network.size(); i++)
                network[i]->updateTimeTick(m_currTime);

  sceneTranslate->translation.setValue(xtrans, ytrans, ztrans);
  //cout<<"ScaleFactor is "<<g_sceneScaleFactor<<endl;
  sceneScale->scaleFactor.setValue(g_sceneScaleFactor,g_sceneScaleFactor,g_sceneScaleFactor);
  if (g_doRotY && g_i_started_spin)
    doRot(g_rotationIncrement, 'y');

  //seismograms->update(nData,eData,zData);
	
  // update marker
  //seismograms->update(speedFactor);
  //velGlyph->updateFaceset(speedFactor);
  //	scenemanager->render();

  SoGLRenderAction * myRenderAction;

  if (g_displayMode == "CLONE")
    {	
      /*	SbViewportRegion region;
		region.setViewportPixels(0, 0, w_width, w_height);
		scenemanager->setViewportRegion(region);

		glDrawBuffer(GL_BACK_LEFT);
		root->whichChild = 0;
		scenemanager->render();

		glDrawBuffer(GL_BACK_RIGHT);
		root->whichChild = 1;
		scenemanager->render();

      */
      glDrawBuffer(GL_BACK_LEFT);
      glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
      //		glDrawBuffer(GL_BACK_RIGHT);
      //		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
  
      SbViewportRegion region;
      region.setViewportPixels(0, 0, w_width, w_height); //L, B, W, H
      //scenemanager->setViewportRegion(region);
      myRenderAction = new SoGLRenderAction(region);
      myRenderAction->setTransparencyType(SoGLRenderAction::SORTED_OBJECT_ADD);

      //glMatrixMode(GL_MODELVIEW);
      //glDisable(GL_CULL_FACE); 
      //		glDrawBuffer(GL_BACK_LEFT);
      //glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
      //scenemanager->render();
      root->whichChild = 0;
      myRenderAction->apply(root);

      glDrawBuffer(GL_BACK_RIGHT);
      glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
 

      //glMatrixMode(GL_MODELVIEW);
      //glDisable(GL_CULL_FACE); 
      //	glDrawBuffer(GL_BACK_RIGHT);
      //	glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
      //	scenemanager->render();
      root->whichChild = 1;
      myRenderAction->apply(root);
		
		
    }
  else
    if (g_displayMode == "STEREO")
      {
		
	SbViewportRegion regionL, regionR;
	regionL.setViewportPixels(0, 0, w_width/2, w_height); //L, B, W, H
	regionR.setViewportPixels(w_width/2, 0, w_width/2, w_height);
	root->whichChild = 0;
	myRenderAction = new SoGLRenderAction(regionL);
	myRenderAction->setTransparencyType(SoGLRenderAction::SORTED_OBJECT_ADD);

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
	region.setViewportPixels(0, 0, w_width, w_height); //L, B, W, H
	myRenderAction = new SoGLRenderAction(region);
	myRenderAction->setTransparencyType(SoGLRenderAction::SORTED_OBJECT_ADD);
	root->whichChild = 0;
        glDisable(GL_CULL_FACE); 
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
	myRenderAction->apply(root);
	//scenemanager->render();
      }

  delete myRenderAction;	

  SoDB::getSensorManager()->processTimerQueue();
  SoDB::getSensorManager()->processDelayQueue(TRUE);
}

void CWindow::DrawOneEye( STEREOVIEW curView)
{//commented out feedback for the timebeing . shalini
	
}

void CWindow::init(string szWindowTitle, string animFile, string configFile)
{

	
}

void CWindow::doRot(float angle, char axis)
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
