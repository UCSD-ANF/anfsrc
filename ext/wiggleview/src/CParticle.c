#include "CParticle.hxx"

CParticle::CParticle()
{
	init();
}

//CParticle::CParticle(SoCoordinate3* ePoints,
//					 SoCoordinate3* nPoints,
//					 SoCoordinate3* zPoints)
CParticle::CParticle(float** ePoints, float** nPoints, float** zPoints,long numPts)
{
	m_numofPointsRead =  numPts;

	m_points = new float*[m_numofPointsRead];

	long i;

    for (i=0; i < m_numofPointsRead; i++)
	{
        m_points[i] = new float[3];
	}

	for (i=0; i < m_numofPointsRead; i++)
	{
		m_points[i][0] = ePoints[i][0];
		m_points[i][1] = nPoints[i][2];
		m_points[i][2] = zPoints[i][1];
	}


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
	//m_headTrans->translation.setValue(
	headSep->addChild(m_headTrans);
	headSep->addChild(headMat);
	headSep->addChild(head);


	m_particleSep->addChild(headSep);
	m_particleSep->addChild(m_scale);
	m_particleSep->addChild(m_trans);
	m_particleSep->addChild(m_rot);
	m_particleSep->addChild(m_mat);
	m_particleSep->addChild(m_coordsLineSet);
	m_particleSep->addChild(light);
	m_particleSep->addChild(m_lineSet);
	

	m_counter = 0;
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


void CParticle::update()
{
	if (m_counter < m_numofPointsRead)
	{
		if (!m_stop)
//		{
			m_counter++;; // later mod - add 10 lines each time
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

//
// scale and translate the channel depending on what is in p - Atul Nov 22
			float maxYe = 0.0f;float maxYn = 0.0f;float maxYz = 0.0f;
			float minYe = 0.0f;float minYn = 0.0f;float minYz = 0.0f;
			
			for ( i = 0; i < p.getNum(); i++)
			{
				SbVec3f aVec = p[i];
				//cout<<"After getting p[i] "<<i<<endl;
				//if (m_amplitudeAxis=='X')
				//{
					if (aVec[0] > maxYe)
						maxYe = aVec[0];
					if (aVec[0] < minYe)
						minYe = aVec[0];
				//}	
				//else
				//	if(m_amplitudeAxis == 'Z')
				//	{
						if (aVec[2] > maxYn)
							maxYn = aVec[2];
						if (aVec[2] < minYn)
							minYn = aVec[2];
				//	}
				//	else
				//		if (m_amplitudeAxis == 'Y')
				//		{
							if (aVec[1] > maxYz)
								maxYz = aVec[1];
							if (aVec[1] < minYz)
								minYz = aVec[1];
				//		}
			}
			//float range = (maxY + minY)/2.0f;
			float scaleVale = 0.0f;
			float scaleValn = 0.0f;
			float scaleValz = 0.0f;
			//float m_stretchAmplitude = 1.0f;
			if (fabsf(maxYe) > fabsf(minYe))
				scaleVale = fabsf(m_stretchAmplitude/maxYe);
			else
				scaleVale = fabsf(m_stretchAmplitude/minYe);
			if (fabsf(maxYn) > fabsf(minYn))
				scaleValn = fabsf(m_stretchAmplitude/maxYn);
			else
				scaleValn = fabsf(m_stretchAmplitude/minYn);
			if (fabsf(maxYz) > fabsf(minYz))
				scaleValz = fabsf(m_stretchAmplitude/maxYz);
			else
				scaleValz = fabsf(m_stretchAmplitude/minYz);

			m_scale->scaleFactor.setValue(scaleVale,scaleValn,scaleValz);
			//

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
	m_stretchAmplitude *= val;
	/*
	SbVec3f scaleVec;
	scaleVec = m_scale->scaleFactor.getValue();
	scaleVec[0] *= val;
	scaleVec[1] *= val;
	scaleVec[2] *= val;
	m_scale->scaleFactor.setValue(scaleVec);
	*/
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
	m_scale->scaleFactor.setValue(east[0],north[1],up[2]);
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

void CParticle::init()
{

//	m_numofPointsRead =  numPts;

	m_points = new float*[5000];

	long i;

    for (i=0; i < 5000; i++)
	{
        m_points[i] = new float[3];
	}

	for (i=0; i < 5000; i++)
	{
		m_points[i][0] = 0.0f;
		m_points[i][1] = 0.0f;
		m_points[i][2] = 0.0f;
	}


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
	//m_headTrans->translation.setValue(
	headSep->addChild(m_headTrans);
	headSep->addChild(headMat);
	headSep->addChild(head);

	SoScale *particleScale = new SoScale;
	particleScale->scaleFactor.setValue(0.01,0.01,0.01);
	SoDrawStyle *drawStyle = new SoDrawStyle;
	drawStyle->lineWidth = 2;

	m_particleSep->addChild(particleScale);
	m_particleSep->addChild(headSep);
	m_particleSep->addChild(m_scale);
	m_particleSep->addChild(m_trans);
	m_particleSep->addChild(m_rot);
	m_particleSep->addChild(m_mat);
	m_particleSep->addChild(m_coordsLineSet);
	m_particleSep->addChild(light);
	m_particleSep->addChild(drawStyle);
	m_particleSep->addChild(m_lineSet);
	

	m_counter = 0;
	m_coordsLineSet->setToDefaults();
	m_numofPointsRead = 0;
	m_stretchAmplitude = 1.0f;
	//float scale = 1e04;
	//m_scale->scaleFactor.setValue(scale, scale, scale);

	m_stop = FALSE;
	m_useSubSet = FALSE;
	m_holdFinal = TRUE;
}

void CParticle::addDataToParticle(string channelId,vector<int> pts)
{
	int i;
	if (channelId == "BHE"|| channelId == "BH2")
	{
		for (i = 0 ; i < 5000; i++)
			m_points[i][0] = 0.0f;
		for (i = 0 ; i < pts.size() && i < 5000; i++)
			m_points[i][0] = pts[i];
	}
	else
		if (channelId == "BHN" || channelId == "BH2")
		{
			for (i = 0 ; i < 5000 ; i++)
				m_points[i][1] = 0.0f;
			for (i = 0 ; i < pts.size() && i < 5000; i++)
				m_points[i][1] = pts[i];
		}
		else
			if (channelId == "BHZ")
			{
				for (i = 0 ; i < 5000; i++)
					m_points[i][2] = 0.0f;
				for (i = 0 ; i < pts.size() && i < 5000; i++)
					m_points[i][2] = pts[i];
			}
	if (pts.size() > m_numofPointsRead)
		m_numofPointsRead = pts.size();
	if (m_numofPointsRead > 5000)
		m_numofPointsRead = 5000;

}

SbVec3f CParticle::getHeadTrans()
{
        return m_headTrans->translation.getValue();
}
