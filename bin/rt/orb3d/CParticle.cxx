#include "CParticle.h"

CParticle::CParticle()
{
   m_particleSep = new SoSeparator;
  m_particleSep->ref();
  cout<<"Created CParticle"<<endl;
  
}

//CParticle::CParticle(SoCoordinate3* ePoints,
//					 SoCoordinate3* nPoints,
//					 SoCoordinate3* zPoints)
CParticle::CParticle(float** ePoints, float** nPoints, float** zPoints,
		     long eNumPts, long nNumPts, long zNumPts)
{
  if (eNumPts > nNumPts)
    if (eNumPts > zNumPts)
      m_numofPointsRead = eNumPts;
    else
      m_numofPointsRead = zNumPts;
  else
    if (nNumPts > zNumPts)
      m_numofPointsRead = nNumPts;
    else
      m_numofPointsRead = zNumPts;
  //m_numofPointsRead =  numPts;

  m_points = new float*[m_numofPointsRead];

  long i;

  for (i=0; i < m_numofPointsRead; i++)
    {
      m_points[i] = new float[3];
    }
  for (i=0; i < m_numofPointsRead; i++)
    {
      m_points[i][0] = 0.0f;
      m_points[i][1] = 0.0f;
      m_points[i][2] = 0.0f;
    }
  for (i=0; i < eNumPts; i++)
    {
      m_points[i][0] = ePoints[i][0];
    }
  for (i=0; i < nNumPts; i++)
    {
      m_points[i][1] = nPoints[i][1];
    }
  for (i=0; i < zNumPts; i++)
    {
      m_points[i][2] = zPoints[i][2];
    }

  /*for (i=0; i < m_numofPointsRead; i++)
    {
    m_points[i][0] = ePoints[i][0];
    m_points[i][1] = nPoints[i][1];
    m_points[i][2] = zPoints[i][2];
    cout<<i<<" : "<<ePoints[i][0]<<" "<<nPoints[i][1]<<" "<<zPoints[i][2]<<endl;
    //m_points[i][1] = nPoints[i][2];
    //m_points[i][2] = zPoints[i][1];
    //m_points[i][1] = zPoints[i][1];
    //m_points[i][2] = nPoints[i][2];
    }*/


  m_particleSep = new SoSeparator;
  m_particleSep->ref();
  //m_pointSet = new SoPointSet;
  //m_coordsPointSet = new SoCoordinate3;
	
  m_scale = new SoScale;
  m_trans = new SoTranslation;
  m_rot   = new SoRotation;
  m_mat = new SoMaterial;

  m_lineSet = new SoLineSet;
  m_coordsLineSet = new SoCoordinate3;

  //SoDrawStyle * drawstyle = new SoDrawStyle; 
  //drawstyle->pointSize = 1; 

  SoLightModel *light = new SoLightModel;
  light->model = SoLightModel::BASE_COLOR;


  // Set up the head of the trace
  SoSphere *head = new SoSphere;
  head->radius.setValue(0.25);

  SoSeparator *headSep = new SoSeparator;
  m_headTrans = new SoTranslation;

  SoMaterial *headMat = new SoMaterial;
  headMat->diffuseColor.setValue(1.0f, 1.0f, 0.0f);
	
  //SoScale *headScale = new SoScale;
  //headScale->scaleFactor.setValue(0.01, 0.01, 0.01);

  //m_headTrans->translation.setValue(
  headSep->addChild(m_headTrans);
  //headSep->addChild(headScale);
  headSep->addChild(headMat);
  headSep->addChild(head);
	
  SoScale *particleScale = new SoScale;
  particleScale->scaleFactor.setValue(0.01, 0.01, 0.01);
	
  SoDrawStyle * drawstyle = new SoDrawStyle;
  drawstyle->lineWidth = 2;

  m_particleSep->addChild(particleScale);
  m_particleSep->addChild(headSep);
  m_particleSep->addChild(m_scale);
  m_particleSep->addChild(m_trans);
  m_particleSep->addChild(m_rot);
  m_particleSep->addChild(m_mat);
  m_particleSep->addChild(m_coordsLineSet);
  m_particleSep->addChild(light); // should be okay to comment this too much light
  m_particleSep->addChild(drawstyle);
  m_particleSep->addChild(m_lineSet);
	

  m_counter = 0;
  m_coordsLineSet->setToDefaults();
	
  //float scale = 1e04;
  //m_scale->scaleFactor.setValue(scale, scale, scale);

  m_stop = FALSE;
  m_useSubSet = FALSE;
  m_holdFinal = TRUE;
}

CParticle::CParticle(float** ePoints, float** nPoints, float** zPoints,
		     long eNumPts, long nNumPts, long zNumPts,
		     double eStart, double nStart, double zStart,double timePeriod)
{
  list<double> startTimes;
  startTimes.push_back(eStart);
  startTimes.push_back(nStart);
  startTimes.push_back(zStart);
  startTimes.sort();
  double earliest = startTimes.front();
  startTimes.pop_front();
  double later = startTimes.front();
  startTimes.pop_front();
  double latest = startTimes.front();
	
  double endN, endE, endZ;
  endE = eStart + (eNumPts * timePeriod);
  endN = nStart + (nNumPts * timePeriod);
  endZ = zStart + (zNumPts * timePeriod);
  list<double> endTimes;
  endTimes.push_back(endE);
  endTimes.push_back(endN);
  endTimes.push_back(endZ);
  endTimes.sort();
  double endLast = endTimes.back();
	
  m_numofPointsRead = ceil((endLast - earliest)/timePeriod);
  m_numofPointsRead++; // TODO : for some reason the if (startAt >= eStart)
  // in the for loops below skip even when startAt == eStart
  // so I allocated an extra float[3] to get by.
  m_points = new float*[m_numofPointsRead];

  int i,j;

  for (i=0; i < m_numofPointsRead; i++)
    {
      m_points[i] = new float[3];
    }
  for (i=0; i < m_numofPointsRead; i++)
    {
      m_points[i][0] = 0.0f;
      m_points[i][1] = 0.0f;
      m_points[i][2] = 0.0f;
    }
  double startAt = earliest;
  for (i=0,j=0; j < eNumPts; startAt+=timePeriod,i++)
    {
      if (startAt >= eStart)
	{
	  m_points[i][0] = ePoints[j][0];
	  j++;
	}
    }
  startAt = earliest;
  for (i=0,j=0; j < nNumPts; startAt+=timePeriod,i++)
    {
      if (startAt >= nStart)
	{
	  m_points[i][1] = nPoints[j][1];
	  j++;
	}
    }
  startAt = earliest;
  for (i=0,j=0; j < zNumPts; startAt+=timePeriod,i++)
    {
      if (startAt >= zStart)
	{
	  m_points[i][2] = zPoints[j][2];
	  j++;
	}
    }

  ofstream out("particle.txt");
  for (i=0; i < m_numofPointsRead; i++)
    {
      out <<"point "<<i<<" "<<m_points[i][0]<<" "<<m_points[i][1]<<" "<<m_points[i][2]<<endl;
    }
  /*for (i=0; i < m_numofPointsRead; i++)
    {
    m_points[i][0] = ePoints[i][0];
    m_points[i][1] = nPoints[i][1];
    m_points[i][2] = zPoints[i][2];
    cout<<i<<" : "<<ePoints[i][0]<<" "<<nPoints[i][1]<<" "<<zPoints[i][2]<<endl;
    //m_points[i][1] = nPoints[i][2];
    //m_points[i][2] = zPoints[i][1];
    //m_points[i][1] = zPoints[i][1];
    //m_points[i][2] = nPoints[i][2];
    }*/

  //	m_glyph = new CGlyph(m_points, m_numofPointsRead);


  m_particleSep = new SoSeparator;
  m_particleSep->ref();
  //m_pointSet = new SoPointSet;
  //m_coordsPointSet = new SoCoordinate3;
	
  m_scale = new SoScale;
  m_trans = new SoTranslation;
  m_rot   = new SoRotation;
  m_mat = new SoMaterial;

  m_lineSet = new SoLineSet;
  m_coordsLineSet = new SoCoordinate3;

  //SoDrawStyle * drawstyle = new SoDrawStyle; 
  //drawstyle->pointSize = 1; 

  SoLightModel *light = new SoLightModel;
  light->model = SoLightModel::BASE_COLOR;


  // Set up the head of the trace
  SoSphere *head = new SoSphere;
  head->radius.setValue(0.25);

  SoSeparator *headSep = new SoSeparator;
  m_headTrans = new SoTranslation;

  SoMaterial *headMat = new SoMaterial;
  headMat->diffuseColor.setValue(1.0f, 1.0f, 0.0f);
	
  //SoScale *headScale = new SoScale;
  //headScale->scaleFactor.setValue(0.01, 0.01, 0.01);

  //m_headTrans->translation.setValue(
  headSep->addChild(m_headTrans);
  //headSep->addChild(headScale);
  headSep->addChild(headMat);
  headSep->addChild(head);
	
  SoScale *particleScale = new SoScale;
  particleScale->scaleFactor.setValue(0.01, 0.01, 0.01);
	
  SoDrawStyle * drawstyle = new SoDrawStyle;
  drawstyle->lineWidth = 2;

  //	m_glyphSwitch = new SoSwitch;
  //	m_glyphSwitch->addChild(new SoSeparator);
  //	m_glyphSwitch->addChild(m_glyph->m_glyphSep);
  //	m_glyphSwitch->whichChild = 1;

  m_particleSep->addChild(particleScale);
  m_particleSep->addChild(headSep);
  m_particleSep->addChild(m_scale);
  m_particleSep->addChild(m_trans);
  m_particleSep->addChild(m_rot);
  //	m_particleSep->addChild(m_glyphSwitch);
  m_particleSep->addChild(m_mat);
  m_particleSep->addChild(m_coordsLineSet);
  //m_particleSep->addChild(light);
  m_particleSep->addChild(drawstyle);
  m_particleSep->addChild(m_lineSet);
	

  m_counter = 0;
  //	m_glyph->m_counter = 0;
  m_coordsLineSet->setToDefaults();
	
  //float scale = 1e04;
  //m_scale->scaleFactor.setValue(scale, scale, scale);

  m_stop = FALSE;
  m_useSubSet = FALSE;
  m_holdFinal = TRUE;
}

CParticle::~CParticle()
{}

SoSeparator* CParticle::getParticleSep()
{
  return m_particleSep;
}

SoPointSet* CParticle::getPointSet()
{
  return m_pointSet;
}

SoLineSet* CParticle::getLineSet()
{
  return m_lineSet;
}

SoCoordinate3* CParticle::getCoordsPointSet()
{
  return m_coordsPointSet;
}

SoCoordinate3* CParticle::getCoordsLineSet()
{
  return m_coordsLineSet;
}


void CParticle::update(int numOfPtsAdded)
{
  if (m_counter < m_numofPointsRead)
    {
      if (!m_stop)
	//		{
	//m_counter++;; // later mod - add 10 lines each time
	m_counter += numOfPtsAdded;
      if (m_counter > m_numofPointsRead)
	m_counter = m_numofPointsRead;

      SoMFVec3f p;
      int i, j;
      if (m_useSubSet == FALSE)
	{
	  for (i = 0; i < m_counter; i++)
	    p.set1Value(i,m_points[i][0], m_points[i][1], m_points[i][2]);
	  m_headTrans->translation.setValue(m_points[m_counter][0], 
					    m_points[m_counter][1], 
					    m_points[m_counter][2]);
	}
      else
	{
	  if (m_counter < m_subSetNum)
	    {
	      for (i = 0; i < m_counter; i++)
		p.set1Value(i,m_points[i][0], m_points[i][1], m_points[i][2]);
	      m_headTrans->translation.setValue(m_points[m_counter][0], 
						m_points[m_counter][1], 
						m_points[m_counter][2]);
	    }
	  else
	    {
	      for (i = m_counter - m_subSetNum, j = 0; j < m_subSetNum; i++,j++)
		p.set1Value(j,m_points[i][0], m_points[i][1],m_points[i][2]);
	      --i;
	      m_headTrans->translation.setValue(m_points[i][0], 
						m_points[i][1], 
						m_points[i][2]);
	    }
	}

      SbVec3f aScale = m_scale->scaleFactor.getValue();
      SbVec3f aTrans = m_headTrans->translation.getValue();
      aTrans[0]= aTrans[0] * aScale[0];
      aTrans[1]= aTrans[1] * aScale[1];
      aTrans[2]= aTrans[2] * aScale[2];
      m_headTrans->translation = aTrans;
			
      m_coordsLineSet->point = p; 
      //		}
    }
  else
    {
      if (!m_holdFinal)
	{
	  m_counter = 0;
	  m_coordsLineSet->setToDefaults();
	  m_stop = TRUE;
	}
    }
	
}

void CParticle::setDiffuseColor(float r, float g, float b)
{
  m_mat->diffuseColor.setValue(r,g,b);
}

void CParticle::increaseScale(float val)
{
  SbVec3f scaleVec;
  scaleVec = m_scale->scaleFactor.getValue();
  scaleVec[0] *= val;
  scaleVec[1] *= val;
  scaleVec[2] *= val;
  m_scale->scaleFactor.setValue(scaleVec);
}

void CParticle::stop()
{
  m_stop = TRUE;
}

void CParticle::start()
{
  m_stop = FALSE;
}

SbBool CParticle::isStopped()
{
  return m_stop;
}

void CParticle::reset()
{
  m_counter = 0;
  m_coordsLineSet->setToDefaults();
  m_headTrans->translation.setValue(0.0f, 0.0f, 0.0f);
}

void CParticle::setGoodLocalScale(float val)
{
  m_goodLocalScale = val;
  m_scale->scaleFactor.setValue(m_goodLocalScale, m_goodLocalScale, m_goodLocalScale);
}

void CParticle::setScale(SbVec3f aVec)
{
  if (aVec[0] > 1)
    m_scale->scaleFactor.setValue(aVec[0], aVec[0], aVec[0]);
  if (aVec[1] > 1)
    m_scale->scaleFactor.setValue(aVec[1], aVec[1], aVec[1]);
  if (aVec[2] > 1)
    m_scale->scaleFactor.setValue(aVec[2], aVec[2], aVec[2]);
}

void CParticle::setScale(SbVec3f east, SbVec3f north, SbVec3f up)
{
  //m_scale->scaleFactor.setValue(east[0],up[1],north[2]);
  m_scale->scaleFactor.setValue(east[0],north[1],up[2]);
  //m_scale->scaleFactor.setValue(east[0],1,1);
  //m_scale->scaleFactor.setValue(1,north[2],1);
}

void CParticle::createSubSetPoints(float numPts)
{
  m_useSubSet = TRUE;
  m_subSetNum = numPts/10;

}

void CParticle::setDelta(float d)
{
  m_delta = d;
}

void CParticle::next()
{
  m_counter++;
}

void CParticle::previous()
{
  m_counter--;
}

// Added May 14 2003
SbVec3f CParticle::getHeadTrans()
{
  //float pts[3];
  return m_headTrans->translation.getValue();
  //return pts;
}
