#include "CSeismometer.h"

// Used in real time version
CSeismometer::CSeismometer()
{
	init();
}

CSeismometer::CSeismometer(string stationName, float lat, float lon,float elev_meters, float min_amplitude, float max_amplitude)
{
	init();
	cout<<stationName <<" "<<lat<<" "<<lon<<endl;
	m_seismometerSep->setName(stationName.c_str());
	m_stationName = stationName;
	m_stationText->string.setValue(stationName.c_str());
	// Position the seismometer depending on the latitude and longitude
	m_latitude = lat;
	m_longitude = lon;
	m_elev_meters = elev_meters;
	m_min_amplitude = min_amplitude;
	m_max_amplitude = m_max_amplitude;
	
	// For flat map
	//m_trans->translation.setValue(0,0,0);
	m_trans->translation.setValue((-116-m_longitude)*10/3, 0,(34 - m_latitude)*10/2);
	//m_trans->translation.setValue(-bhz->getLongitude()*0.00278746, bhz->getLatitude()*0.00278746, -0.05);
	
	bhn->setMinMaxAmplitude(m_min_amplitude, m_max_amplitude);	
	bhe->setMinMaxAmplitude(m_min_amplitude, m_max_amplitude);	
	bhz->setMinMaxAmplitude(m_min_amplitude, m_max_amplitude);	
	
}

CSeismometer::~CSeismometer()
{}


// // Changed May 15 2003
// //void CSeismometer::update(float curTime, SbBool drawOnGlobe, int numOfPtsAdded, SbBool quickPlay)
// void CSeismometer::update(SbTime now, SbBool drawOnGlobe, int numOfPtsAdded, SbBool quickPlay)
// {
// 	if (drawOnGlobe)
// 	{
// 		m_trans->translation.setValue(m_sphereTrans[0], m_sphereTrans[1], m_sphereTrans[2]);
// 		m_rot->rotation.setValue(m_axis,m_angle);
// 		// Added May 14, 03 for lollypop
// 		m_lollypoints.set1Value(0, 0, 0, 0);
// 		m_lollypoints.set1Value(1, 0, 0, 0);
// 	}
// 	else
// 	{
// 		//float x = (bhz->getLongitude()-25)*0.25*10;
// 		//float y = (bhz->getLatitude()-43)*0.33*10;
// 		//m_trans->translation.setValue(x, y, -0.05);
// 		m_trans->translation.setValue(-bhz->getLongitude()*0.00278746, bhz->getLatitude()*0.00278746, -0.05);
// 		m_rot->rotation.setValue(0,0,0,1);
// 		// Added May 14, 03 for lollypop
// 		m_lollypoints.set1Value(0, 0, 0, 0.05);
// 		m_lollypoints.set1Value(1, 0, 0, 0);

// 	}
// 	// Added May 14
// 	m_coordsLineSet->point = m_lollypoints; 
// 	SoMFVec3f p;
// 	p.set1Value(0,0,0,0);
// 	SbVec3f pts = particle->getHeadTrans();
// 	p.set1Value(1,pts[0], pts[1], pts[2]);
// 	m_coordsLineToHead->point = p;

// 	// finished adding 

// 	// May 15 2003 - not sure if it is still UT time
// 	// Get the current UT time in seconds from the parameter passed
// 	float curTime = now.getValue();
// 	if (curTime >= m_startTime)
// 	{
// 		if (curTime < m_startTime+10)
// 		{
// 			string station = bhe->getStationName().c_str();
// 			cout <<  station << " started recording : Start time "<<m_startTime<<" "<<endl;
// 		}
// 		if (quickPlay == TRUE)
// 		{
// 			// May 15 2003 Added 
// 			SbTime diff;
// 			diff = now - m_prevTime;
// 			//numOfPtsAdded = 1;
// 			numOfPtsAdded = diff.getValue()/bhe->getDelta();
// 			//numOfPtsAdded = diff.getValue()/bhe->m_xUnit;
// 			if (numOfPtsAdded < 1) // Make sure that at least one point
// 				numOfPtsAdded = 1; //is added, in case user starts pressing -
// 					// right away
// 		}

// 		// Changed May 15 2003
// 		// Check each channel too ??? 
// 		if (curTime >= m_startTimeZ)	// Check each channel too 
// 			bhz->update(numOfPtsAdded);
// 			//bhz->updateSCEC(numOfPtsAdded);
// 		if (curTime >= m_startTimeN)
// 			bhn->update(numOfPtsAdded);
// 			//bhn->updateSCEC(numOfPtsAdded);
// 		if (curTime >= m_startTimeE)
// 			bhe->update(numOfPtsAdded);
// 			//bhe->updateSCEC(numOfPtsAdded);
// 		// Finished change

// 		//particle->setScale(bhe->getScale(), bhn->getScale(),bhz->getScale());
// 		//particle->update(numOfPtsAdded);
// 	}
// 	m_prevTime = now;
// }


SoSeparator* CSeismometer::getSep()
{
	return m_seismometerSep;
}

void CSeismometer::stretchAmplitudeAxis(float val)
{
	bhe->stretchAmplitudeAxis(val);
	bhz->stretchAmplitudeAxis(val);
	bhn->stretchAmplitudeAxis(val);
	particle->increaseScale(val);
}

void CSeismometer::stretchTimeAxis(float val)
{
	//cout<<"CSeismometere::stretchTimeAxis"<<endl;
	bhe->stretchTimeAxis(val);
	bhz->stretchTimeAxis(val);
	bhn->stretchTimeAxis(val);
}

void CSeismometer::toggleParticle()
{
	//cout<<"Ref count on m_particleSwitch "<<m_particleSwitch->getRefCount()<<endl;;
	if (m_particleSwitch->whichChild.getValue() == 0)
		//m_particleSwitch->whichChild = SO_SWITCH_NONE;
		m_particleSwitch->whichChild = 1;
	else
		m_particleSwitch->whichChild = 0;
	/*
	
	SoSwitch *aSwitch = new SoSwitch;
	aSwitch = mySearch->get("particleSwitch");
	if (aSwitch->whichChild.getValue() == 0)
		return TRUE;
	else
		return FALSE;
		*/
}

void CSeismometer::toggleWiggles()
{
	//cout<<"Ref count on m_wiggleSwitch "<<m_wiggleSwitch->getRefCount()<<endl;
	if (m_wiggleSwitch->whichChild.getValue() == 0)
		m_wiggleSwitch->whichChild = SO_SWITCH_NONE;
	else
		m_wiggleSwitch->whichChild = 0;
	/*
	CSearch *mySearch = new CSearch(m_seismometerSep);
	SoSwitch *aSwitch = new SoSwitch;
	aSwitch = mySearch->get("wiggleSwitch");
	if (aSwitch->whichChild.getValue() == 0)
		return TRUE;
	else
		return FALSE;
		*/
}

void CSeismometer::start()
{
	
	bhe->start();
	bhn->start();
	bhz->start();
	particle->start();
}

void CSeismometer::stop()
{
	bhe->stop();
	bhn->stop();
	bhz->stop();
	particle->stop();
}

void CSeismometer::reset()
{
	bhe->reset();
	bhn->reset();
	bhz->reset();
	particle->reset();
}

void CSeismometer::next()
{
	bhe->next();
	bhn->next();
	bhz->next();
	particle->next();
}

void CSeismometer::previous()
{
	bhe->previous();
	bhn->previous();
	bhz->previous();
	particle->previous();
}

SbBool CSeismometer::isFinished()
{
	if (bhz->isFinished() && bhe->isFinished() && bhn->isFinished())
		return TRUE;
	else
		return FALSE;
}

//void CSeismometer::addChannel(CChannel *someChannel)
//{
// 	string channel = someChannel->getChannelId();
// 	if (channel == "BHE")
// 	{
// 		bhe = someChannel;
// 		m_wiggleSwitch->addChild(bhe->getChannelSep());
// 	}
// 	else
// 		if (channel == "BHN")
// 		{
// 			bhn = someChannel;
// 			m_wiggleSwitch->addChild(bhn->getChannelSep());
// 		}
// 		else
// 			if (channel == "BHZ")
// 			{
// 				bhz = someChannel;
// 				m_wiggleSwitch->addChild(bhz->getChannelSep());
// 			}
//}


string CSeismometer::getStationName()
{
	return m_stationName;
}

void CSeismometer::init()
{

  // Create the root node m_SeismometerSep
  cout<<"Inside CSeismometer::init()"<<endl;
	m_seismometerSep = new SoSeparator;
	m_seismometerSep->ref();

	// Translation node
	m_trans = new SoTranslation;

	// Create the grey sphere that represents the station
	SoSeparator *sSep = new SoSeparator;
	// Material properties of sphere
	SoMaterial *sMat = new SoMaterial;
	sMat->diffuseColor.setValue(0.5f, 0.5f, 0.5f);
	sMat->emissiveColor.setValue(0.5f, 0.5f, 0.5f);
	sMat->transparency.setValue(0.7f);
	m_coordsLineSet = new SoCoordinate3;
	m_lollypoints.set1Value(0, 0, 0, 0.05);
	m_lollypoints.set1Value(1, 0, 0, 0);
	m_coordsLineSet->point = m_lollypoints;
	SoLightModel *light = new SoLightModel;
	light->model = SoLightModel::BASE_COLOR;
	SoDrawStyle * drawstyle = new SoDrawStyle; 
	drawstyle->lineWidth = 2;
	SoLineSet *s_lineSet = new SoLineSet;
	SoScale *sScale = new SoScale;
	sScale->scaleFactor.setValue(0.01, 0.01, 0.01);
	SoSphere *s = new SoSphere;
	s->ref();
	sSep->addChild(sMat);
	sSep->addChild(m_coordsLineSet); /* Adding m_coordsLineSet, light,*/
	sSep->addChild(light);			 /* drawstyle, new SoLineSet May 14, 03*/
	sSep->addChild(drawstyle);		 /* why new SoLineSet dunno */
	sSep->addChild(new SoLineSet);
	sSep->addChild(sScale);
	sSep->addChild(s);

	// The station name displayed as text
	m_stationText = new SoText2;

	// Time Ticks
	//m_timeTick = new CTimeTick();
	int y = 0;
	for (int i = 0 ; i < 6; i++, y +=2.4)
	{
		CTimeTick *aTimeTick = new CTimeTick("reading..", 0.2, 0 ,0);

		m_timeTicks.push_back(aTimeTick);
	}
	// Drawstyle
	SoDrawStyle *aDrawStyle = new SoDrawStyle;
        aDrawStyle->lineWidth = 2;

	// The channels
	cout<<"Making new channels "<<endl;
	bhe = new CChannel("BHE",1,1,1);
	bhz = new CChannel("BHZ",1, 0.5, 0.5 );
	bhn = new CChannel("BHN",0,1,0);

	cout<<"Making m_wiggleSwitch"<<endl;
	m_wiggleSwitch = new SoSwitch();
	m_wiggleSwitch-> setName("wiggleSwitch");
	SoSeparator *wiggleSeparator = new SoSeparator;
	wiggleSeparator->addChild(bhe->getChannelSep());
	wiggleSeparator->addChild(bhn->getChannelSep());
	wiggleSeparator->addChild(bhz->getChannelSep());
	m_wiggleSwitch->addChild(wiggleSeparator);
	m_wiggleSwitch->whichChild = 0;

	// The particle
	cout<<"Making m_particleSwitch"<<endl;
	m_particleSwitch = new SoSwitch();
	m_particleSwitch->setName("particleSwitch");
	// SoSeparator *particleSep = new SoSeparator;
// 	SoScale *particleScale = new SoScale;
// 	particleScale->scaleFactor.setValue(0.01, 0.01, 0.01);
// 	// get the particle head translation and then draw a line from the center
// 	// of the gray sphere to the head, so that you know where it is going
// 	m_coordsLineToHead = new SoCoordinate3;
// 	SoMFVec3f p;
// 	p.set1Value(0,0,0,0);
// 	SbVec3f pts = particle->getHeadTrans();
// 	p.set1Value(1,pts[0], pts[1], pts[2]);
// 	m_coordsLineToHead->point = p;
	
// 	particleSep->addChild(particle->getParticleSep());
	//	particleSep->addChild(particleScale);
	//	particleSep->addChild(sMat);
	//	particleSep->addChild(m_coordsLineToHead);
	//	particleSep->addChild(light);
	//	particleSep->addChild(drawstyle);
	//	particleSep->addChild(new SoLineSet);

// 	m_particleSwitch = new SoSwitch();
// 	m_particleSwitch->setName("particleSwitch");
// 	m_particleSwitch->addChild(particleSep);
// 	// Adding  particleSep as a child instead. This is for the line
// 	// from center of station to head of particle.
// 	m_particleSwitch->addChild(new SoSeparator);
// 	m_particleSwitch->whichChild = 0;
		

	// Set up the Seismometer
	m_seismometerSep->addChild(m_trans);
	m_seismometerSep->addChild(sSep);
	m_seismometerSep->addChild(m_stationText);
	for (int i = 0; i < 6; i++)
		m_seismometerSep->addChild(m_timeTicks[i]->m_timeTickSep);
	m_seismometerSep->addChild(aDrawStyle);
	m_seismometerSep->addChild(m_wiggleSwitch);
// 	m_seismometerSep->addChild(m_particleSwitch);
	cout<<"Seismometer set up"<<endl;
	
}

void CSeismometer::addDataToChannel(string channelId, int numPts, float xUnit, float sampRate, vector<float> pts, double currTime, double pktTime)
{
       	if (channelId == "BHZ")
	{
		bhz->addDataToChannel(channelId,numPts,xUnit,sampRate,pts, currTime, pktTime);
	}
	else
	if (channelId == "BHN")
	{
		bhn->addDataToChannel(channelId,numPts,xUnit,sampRate,pts, currTime, pktTime);
	}
	else
	if (channelId == "BHE")
	{
		bhe->addDataToChannel(channelId,numPts,xUnit,sampRate,pts, currTime, pktTime);
	}
	
}

void CSeismometer::scrollTimeAxis(int shift)
{
	bhn->scrollTimeAxis(shift);
	bhe->scrollTimeAxis(shift);

}

void CSeismometer::updateTimeTick(SbTime currTime)
{
	SbTime oneMinute(60);
	for (int i = 0; i < 6; i++) {
		string timeStr(currTime.formatDate("%F.%T").getString());
		//string timeStr(currTime.format("%H.%M.%S").getString());
		m_timeTicks[i]->updateTimeText(timeStr);
		currTime -= oneMinute;
	}
}
