#include "CSeismometer.hxx"

CSeismometer::CSeismometer(string configFile)
{
	init(configFile);
	//float latitude = 0.0f;
	//float longitude = 0.0f;
	/*m_trans->translation.setValue(cos(DTOR(longitude))*sin(DTOR(latitude)),
				sin(DTOR(longitude))*sin(DTOR(latitude)),
				cos(DTOR(latitude)));
*/
}

CSeismometer::CSeismometer(string configFile, int stationNum)
{

	string station;
#ifdef linux
	char *a;
	a = intoa(stationNum);
	station = "Station";
	station += a; 
#endif
#ifdef WIN32
	char buffer [33];
	itoa (stationNum,buffer,10);
	station = "Station";
	station+= buffer;
#endif


	CSearch mySearch(configFile);
	float *diffuseColor;
	diffuseColor = new float[3];

	m_seismometerSep = new SoSeparator;
	m_seismometerSep->ref();

	bhz = new CChannel(configFile,'Z', station);
	bhz->parseFile();

	
	bhn = new CChannel(configFile,'N', station);
	bhn->parseFile();
	
	bhe = new CChannel(configFile,'E', station);
	bhe->parseFile();
	
	particle = new CParticle(bhe->getPoints(), 
							 bhn->getPoints(),
							 bhz->getPoints(),
							 bhe->getNumPointsRead());
	particle->setScale(bhz->getScale());
	particle->setDelta(bhz->getDelta());

	m_startTime = bhz->getStartTime();

	string useAllPts;
	mySearch.get("UseAllPoints", useAllPts);
	if (useAllPts == "NO")
	{
		float subSetNum;
		mySearch.get("NumOfPoints", subSetNum);
		bhz->createSubSetPoints(subSetNum);
		bhe->createSubSetPoints(subSetNum);
		bhn->createSubSetPoints(subSetNum);
		particle->createSubSetPoints(subSetNum);
	}

	string wiggleDir;
	mySearch.get("WiggleDirection", wiggleDir);
	bhz->setWiggleDir(wiggleDir);
	bhe->setWiggleDir(wiggleDir);
	bhn->setWiggleDir(wiggleDir);
	

	/*
	string scaleType;
	mySearch.get("UseScale", scaleType);
	if (scaleType == "COMMON")
		else
		if (scaleType == "GOOD_LOCAL")
			particle->setGoodLocalScale(bhe->getGoodLocalScale());
		else
			if (scaleType == "NORMALIZED_LOCAL")
	*/		

	mySearch.get("ParticleMaterial", diffuseColor);
	particle->setDiffuseColor(diffuseColor[0],diffuseColor[1],diffuseColor[2]);


	mySearch.get("NMaterial", diffuseColor);
	bhn->setDiffuseColor(diffuseColor[0],diffuseColor[1],diffuseColor[2]);
	mySearch.get("EMaterial", diffuseColor);
	bhe->setDiffuseColor(diffuseColor[0],diffuseColor[1],diffuseColor[2]);
	mySearch.get("ZMaterial", diffuseColor);
	bhz->setDiffuseColor(diffuseColor[0],diffuseColor[1],diffuseColor[2]);

	// Position the seismometer depending on the latitude and longitude

	float latitude = bhz->getLatitude();
	float longitude = bhz->getLongitude();

	m_trans = new SoTranslation;
	// For flat map
	m_trans->translation.setValue(longitude, 5,-latitude);
	// For globe
	
	/*m_trans->translation.setValue(cos(DTOR(longitude))*sin(DTOR(latitude)),
				sin(DTOR(longitude))*sin(DTOR(latitude)),
				cos(DTOR(latitude)));
	*/
	m_wiggleSwitch = new SoSwitch();

	m_wiggleSwitch->setName("wiggleSwitch");
	SoSeparator *wiggleSeparator = new SoSeparator;
	wiggleSeparator->addChild(bhe->getChannelSep());
	wiggleSeparator->addChild(bhn->getChannelSep());
	wiggleSeparator->addChild(bhz->getChannelSep());
	m_wiggleSwitch->addChild(wiggleSeparator);
	m_wiggleSwitch->whichChild = 0;


	m_particleSwitch = new SoSwitch();
	m_particleSwitch->setName("particleSwitch");
	m_particleSwitch->addChild(particle->getParticleSep());
	m_particleSwitch->addChild(new SoSeparator);
	m_particleSwitch->whichChild = 0;
	
	SoSeparator *sSep = new SoSeparator;
	SoMaterial *sMat = new SoMaterial;
	sMat->diffuseColor.setValue(0.5f, 0.5f, 0.5f);
	sMat->emissiveColor.setValue(0.5f, 0.5f, 0.5f);
	sMat->transparency.setValue(0.7f);
	SoSphere *s = new SoSphere;
	sSep->addChild(sMat);
	sSep->addChild(s);

	m_stationText = new SoText2;
	m_stationText->string.setValue(bhe->getStationName().c_str());


	m_seismometerSep->addChild(m_trans);
	m_seismometerSep->addChild(sSep);
	m_seismometerSep->addChild(m_stationText);
	m_seismometerSep->addChild(m_wiggleSwitch);
	m_seismometerSep->addChild(m_particleSwitch);
	//m_seismometerSep->addChild(bhe->getChannelSep());
	//m_seismometerSep->addChild(bhn->getChannelSep());
	//m_seismometerSep->addChild(bhz->getChannelSep());
	//m_seismometerSep->addChild(particle->getParticleSep());

	
}

CSeismometer::~CSeismometer()
{}

void CSeismometer::update(SbBool drawOnGlobe)
{
	if (drawOnGlobe)
	{
		m_trans->translation.setValue(m_sphereTrans[0], m_sphereTrans[1], m_sphereTrans[2]);
		m_rot->rotation.setValue(m_axis,m_angle);
	}
	else
	{
	//	m_trans->translation.setValue(-bhz->getLongitude()*0.00278746, bhz->getLatitude()*0.00278746,-0.05);
		m_trans->translation.setValue(-2*(bhz->getLongitude()+115.0+2.0), 2*(bhz->getLatitude()-32.0-1.50), -0.05);
		m_rot->rotation.setValue(0,0,0,1);
	}

	bhz->update();
	bhn->update();
	bhe->update();
	//particle->setScale(bhe->getScale(), bhn->getScale(), bhz->getScale());
	particle->update();
}

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
	CSearch *mySearch = new CSearch(m_seismometerSep);
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
	if (bhz->isFinished())
		return TRUE;
	else
		return FALSE;
}

void CSeismometer::addChannel(CChannel *someChannel)
{
	string channel = someChannel->getChannelId();
	if (channel == "BHE")
	{
		bhe = someChannel;
		m_wiggleSwitch->addChild(bhe->getChannelSep());
	}
	else
		if (channel == "BHN")
		{
			bhn = someChannel;
			m_wiggleSwitch->addChild(bhn->getChannelSep());
		}
		else
			if (channel == "BHZ")
			{
				bhz = someChannel;
				m_wiggleSwitch->addChild(bhz->getChannelSep());
			}
}

string CSeismometer::getStationId()
{
	return m_stationId;
}

string CSeismometer::getStationName()
{
	return m_stationName;
}

void CSeismometer::init(string configFile)
{

	m_seismometerSep = new SoSeparator;
	m_seismometerSep->ref();

	m_trans = new SoTranslation;

	m_wiggleSwitch = new SoSwitch();
	m_wiggleSwitch-> setName("wiggleSwitch");
	m_stationText = new SoText2;

	bhe = new CChannel(configFile,'e');
	bhz = new CChannel(configFile, 'z');
	bhn = new CChannel(configFile, 'n');
	particle = new CParticle();

	SoSeparator *sSep = new SoSeparator;
	SoMaterial *sMat = new SoMaterial;
	sMat->diffuseColor.setValue(0.5f, 0.5f, 0.5f);
	sMat->emissiveColor.setValue(0.5f, 0.5f, 0.5f);
	sMat->transparency.setValue(0.7f);
	SoSphere *s = new SoSphere;
	SoScale *sScale = new SoScale;
	sScale->scaleFactor.setValue(0.01,0.01,0.01);
	sSep->addChild(sMat);
	sSep->addChild(sScale);
	sSep->addChild(s);
	
	m_rot = new SoRotation;

	m_particleSwitch = new SoSwitch();
	m_particleSwitch->setName("particleSwitch");
	m_particleSwitch->addChild(particle->getParticleSep());
	m_particleSwitch->addChild(new SoSeparator);
	m_particleSwitch->whichChild = 0;

	m_seismometerSep->addChild(m_trans);
	m_seismometerSep->addChild(m_rot);
	m_seismometerSep->addChild(sSep);
	m_seismometerSep->addChild(m_stationText);
	m_seismometerSep->addChild(m_wiggleSwitch);
	m_seismometerSep->addChild(m_particleSwitch);
	
	
//	m_wiggleSwitch->setName("wiggleSwitch");
	SoScale *wiggleScale = new SoScale;
	wiggleScale->scaleFactor.setValue(0.01, 0.01, 0.01);

	SoSeparator *wiggleSeparator = new SoSeparator;
	wiggleSeparator->addChild(wiggleScale);
	wiggleSeparator->addChild(bhe->getChannelSep());
	wiggleSeparator->addChild(bhn->getChannelSep());
	wiggleSeparator->addChild(bhz->getChannelSep());
	m_wiggleSwitch->addChild(wiggleSeparator);
	m_wiggleSwitch->whichChild = 0;



	CSearch * mySearch = new CSearch(configFile);
	string useAllPts;
	mySearch->get("UseAllPoints", useAllPts);
	if (useAllPts == "NO")
	{
		float subSetNum;
		mySearch->get("NumOfPoints", subSetNum);
		bhz->createSubSetPoints(subSetNum);
		bhe->createSubSetPoints(subSetNum);
		bhn->createSubSetPoints(subSetNum);
		particle->createSubSetPoints(subSetNum);
	}
	string wiggleDir;
	mySearch->get("WiggleDirection", wiggleDir);
	bhz->setWiggleDir(wiggleDir);
	bhe->setWiggleDir(wiggleDir);
	bhn->setWiggleDir(wiggleDir);
	
	float *diffuseColor;
	diffuseColor = new float[3];
	mySearch->get("NMaterial", diffuseColor);
	bhn->setDiffuseColor(diffuseColor[0],diffuseColor[1],diffuseColor[2]);
	mySearch->get("EMaterial", diffuseColor);
	bhe->setDiffuseColor(diffuseColor[0],diffuseColor[1],diffuseColor[2]);
	mySearch->get("ZMaterial", diffuseColor);
	bhz->setDiffuseColor(diffuseColor[0],diffuseColor[1],diffuseColor[2]);
	mySearch->get("ParticleMaterial", diffuseColor);
	particle->setDiffuseColor(diffuseColor[0],diffuseColor[1],diffuseColor[2]);

	m_haveNewData = FALSE;
	delete diffuseColor;
	delete mySearch;
	
}

void CSeismometer::addDataToChannel(string stationId, string siteId, string channelId ,
       float latitude, float longitude, float sampling, vector<int> pts)
{
	m_stationName = stationId;
	m_stationText->string.setValue(m_stationName.c_str());

	m_seismometerSep->setName(m_stationName.c_str());
	
	float sphereRadius = 1.05f;
	m_sphereTrans[0] = sphereRadius * sin(DTOR(longitude))*sin(DTOR(90-latitude));
	m_sphereTrans[1] = sphereRadius * cos(DTOR(90-latitude));
	m_sphereTrans[2] = sphereRadius * cos(DTOR(longitude))*sin(DTOR(90-latitude));
	//if (g_drawOnGlobe)
		m_trans->translation.setValue(m_sphereTrans[0], m_sphereTrans[1], m_sphereTrans[2]);
	//else
	//	m_trans->translation.setValue(-bhz->getLongitude()*0.00278746, bhz->getLatitude()*0.00278746, -0.05);

	float zAxis[] = {0.0f, 0.0f,1.0f};
	float xAxis[] = {1.0f, 0.0f, 0.0f};
	float yAxis[] = {0.0f, 1.0f, 0.0f};
	
	m_axis.setValue(yAxis[0], yAxis[1], yAxis[2]);
	float proj[3];
	projectionBonA(yAxis,m_sphereTrans,proj);
	float dir[3];
	dir[0] = -proj[0] + m_sphereTrans[0];
	dir[1] = -proj[1] + m_sphereTrans[1];
	dir[2] = -proj[2] + m_sphereTrans[2];
	m_angle = calcAngle(zAxis, dir);


	if (channelId == "BHZ")
	{
		bhz->addDataToChannel(stationId,siteId,channelId,latitude,
				longitude,sampling,pts);
		particle->addDataToParticle(channelId,pts);
		//bhz->setDiffuseColor(1.0, 0.0, 0.0);
	}
	else
	//	if (channelId == "BHE" || channelId == "BH1")
		if (channelId == "BHE")
		{
			bhe->addDataToChannel(stationId,siteId,channelId,latitude,
			        longitude,sampling,pts);
			particle->addDataToParticle(channelId,pts);
			//bhe->setDiffuseColor(0.0, 1.0, 0.0);
		}
		else
			//if (channelId =="BHN" || channelId == "BH2")
			if (channelId =="BHN")
			{
				bhn->addDataToChannel(stationId,siteId,channelId,latitude,
					longitude,sampling,pts);
				particle->addDataToParticle(channelId,pts);
				//bhe->setDiffuseColor(0.0, 0.0, 1.0);
			}
}

SbBool CSeismometer::haveNewData()
{
	return m_haveNewData;
}

void CSeismometer::setHaveNewData(SbBool aFlag)
{
	m_haveNewData = aFlag;
}
