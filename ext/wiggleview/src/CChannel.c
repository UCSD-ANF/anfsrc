#include "CChannel.hxx"

CChannel::CChannel(string configFileName, char channelId)
{
	init(configFileName,channelId);
}
CChannel::CChannel(string fName):m_fileName(fName)
{
	m_channelSep = new SoSeparator;
	m_channelSep->ref();
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


	m_channelSep->addChild(m_scale);
	m_channelSep->addChild(m_trans);
	m_channelSep->addChild(m_rot);
	m_channelSep->addChild(m_mat);
	m_channelSep->addChild(m_coordsLineSet);
	m_channelSep->addChild(light);
	m_channelSep->addChild(m_lineSet);
	

	m_counter = 0;

	m_stop = FALSE;
	m_useSubSet = FALSE;

}

CChannel::CChannel(string configFileName, char channelId, string station)
{

	m_stationId = station;
	CSearch * mySearch = new CSearch(configFileName);

	string goodLocalScale(m_stationId);
	goodLocalScale+= "Scale";
	mySearch->get(goodLocalScale, m_goodLocalScale);

	switch (channelId)
	{
		case 'n':
		case 'N':
			{
				string nFile = m_stationId + "N";
				mySearch->get(nFile, m_fileName);
				mySearch->get("NTimeAxis", m_timeAxis);
				mySearch->get("NAmplitudeAxis", m_amplitudeAxis);
				break;
			}
	case 'e':
	case 'E':
		{
			string eFile = m_stationId + "E";
			mySearch->get(eFile, m_fileName);
			mySearch->get("ETimeAxis", m_timeAxis);
			mySearch->get("EAmplitudeAxis", m_amplitudeAxis);
			break;
		}
	case 'z':
	case 'Z':
		{
			string zFile = m_stationId + "Z";
			mySearch->get(zFile, m_fileName);
			mySearch->get("ZTimeAxis", m_timeAxis);
			mySearch->get("ZAmplitudeAxis", m_amplitudeAxis);
			break;
		}
	default:
		break;
	}

	mySearch->get("UseScale", m_scaleType);

	m_channelSep = new SoSeparator;
	m_channelSep->ref();
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


	m_channelSep->addChild(m_scale);
	m_channelSep->addChild(m_trans);
	m_channelSep->addChild(m_rot);
	m_channelSep->addChild(m_mat);
	m_channelSep->addChild(m_coordsLineSet);
	m_channelSep->addChild(light);
	m_channelSep->addChild(m_lineSet);
	

	m_counter = 0;
	
	m_stop = FALSE;
	m_useSubSet = FALSE;
	m_holdFinal = TRUE;
}

CChannel::CChannel(string stationId, string siteId, string channelId , 
		float latitude, float longitude, float sampling, vector<int> pts,string configFile,char channelChar)
//CChannel::CChannel(string stationId, string siteId, string channelId, int num, int* pts)
{
	// m_stationName is the name ie. ANMO, SJG etc
	// m_stationId is Station1, Station2 etc
	m_stationName = stationId;
	m_siteId = siteId;
	m_channelId = channelId;
	m_latitude = latitude;
	m_longitude = longitude;
	init(configFile,channelChar);
	int i;
	m_points = new float*[pts.size()];
	for (i = 0; i < pts.size(); i++)
		m_points[i] = new float[3];

	float x=0.0f; float z=0.0f;
	float xInterval = 0.05f; // TODO : Get exact value from data	
	float scaleFactor = 1e+09;
	float maxY = 0.0f;
	float minY = 0.0f;
	float range = 0.0f;
	SoMFVec3f p;
	if (m_channelId == "BHE" || m_channelId == "BH1")
	{
		m_timeAxis = 'Z';
		m_amplitudeAxis = 'X';
		//for (i=0; i < m_numofPointsRead; i++)
		for (i=0; i < pts.size(); i++)
	        {
	         // Draw along X-Z plane : 
		         m_points[i][2] = x;
			 //m_points[i][0] = inData[i]/scaleFactor;
			 m_points[i][0] = pts[i]/scaleFactor;
			 m_points[i][1] = z;
			 x+=xInterval; // so now using the first field
			if (m_points[i][0] > maxY)
			       maxY = m_points[i][0];
			if (m_points[i][0] < minY)
				minY = m_points[i][0];	
			p.set1Value(i,m_points[i][0],m_points[i][1],m_delta*i);
	         }
		 range = (maxY - minY)/scaleFactor;
	         float shift = (maxY/scaleFactor)- (range/2);
		 m_trans->translation.setValue(-shift, 0 , 0);

	}
	else
		if (m_channelId == "BHN" || m_channelId == "BH2")
		{
			m_timeAxis = 'Y';
			m_amplitudeAxis = 'Z';

			//for (i=0; i < m_numofPointsRead; i++)
			for (i=0; i < pts.size(); i++)
	                {
	                // Draw along Y-Z plane 
		                 m_points[i][1] = x;
				 //m_points[i][2] = inData[i]/scaleFactor;
				 m_points[i][2] = pts[i]/scaleFactor;
				 m_points[i][0] = z;
				 x+=xInterval; // so now using the first field 
				if (m_points[i][2] > maxY)
			       		maxY = m_points[i][2];
				if (m_points[i][2] < minY)
					minY = m_points[i][2];	
				p.set1Value(i,m_points[i][0],m_points[i][1],m_delta*i);
			}
		 	range = (maxY - minY)/scaleFactor;
			float shift = (maxY/scaleFactor)- (range/2);
			m_trans->translation.setValue(0, 0, -shift);
		}
		else
			if (m_channelId == "BHZ")
			{
				m_timeAxis = 'X';
				m_amplitudeAxis = 'Y';
				//for (i=0; i < m_numofPointsRead; i++)
				for (i=0; i < pts.size(); i++)
		                {
		                  // Draw along X-Y plane : normal
		                     m_points[i][0] = x;
				     //m_points[i][1] = inData[i]/scaleFactor;
				     m_points[i][1] = pts[i]/scaleFactor;
				     m_points[i][2] = z;
				     x+=xInterval; // so now using the first field 
			       	     if (m_points[i][2] > maxY)
			       		maxY = m_points[i][2];
				     if (m_points[i][2] < minY)
					minY = m_points[i][2];	
			  	     p.set1Value(i,m_points[i][0],m_points[i][1],m_delta*i);
				}
		 		range = (maxY - minY)/scaleFactor;
				float shift = (maxY/scaleFactor)- (range/2);
				m_trans->translation.setValue(0, -shift, 0);
			}

	m_coordsLineSet->point = p;
	float maxAmplitude;
	if (maxY > abs(minY))
		maxAmplitude = maxY;
	else
		maxAmplitude = abs(minY);
	// Another place where you can scale the data
	
	switch (m_amplitudeAxis)
	{
		case 'X':
		{
			if (m_scaleType == "COMMON")
				m_scale->scaleFactor.setValue(1e04, 1, 1); //  X-Y plane
			if (m_scaleType == "GOOD_LOCAL")
			        m_scale->scaleFactor.setValue(m_goodLocalScale, 1, 1); //  X-Y plane
			if (m_scaleType == "NORMALIZED_LOCAL")
			        m_scale->scaleFactor.setValue(scaleFactor/maxAmplitude, 1, 1); //  X-Y plane
			break;
		}
		case 'Y':
		{
			if (m_scaleType == "COMMON")
				m_scale->scaleFactor.setValue(1, 1e04, 1); //  X-Y plane
			if (m_scaleType == "GOOD_LOCAL")
			        m_scale->scaleFactor.setValue(1, m_goodLocalScale, 1); //  X-Y plane
		        if (m_scaleType == "NORMALIZED_LOCAL")
		                m_scale->scaleFactor.setValue(1, scaleFactor/maxAmplitude, 1); //  X-Y plane
		        break;
		}
		case 'Z':
		{
			if (m_scaleType == "COMMON")
		                m_scale->scaleFactor.setValue(1,1, 1e04); // Y-Z plane
		        if (m_scaleType == "GOOD_LOCAL")
		                m_scale->scaleFactor.setValue(1,1, m_goodLocalScale); // Y-Z plane
		        if (m_scaleType == "NORMALIZED_LOCAL")
			        m_scale->scaleFactor.setValue(1,1, scaleFactor/maxAmplitude); // Y-Z plane
		        break;
		}
		default:
			break;
	}
		
}


void CChannel::init(string configFile, char channelId)
{
	m_channelSep = new SoSeparator;
	m_channelSep->ref();
	m_scale = new SoScale;
	m_trans = new SoTranslation;
	m_rot   = new SoRotation;
	m_mat = new SoMaterial;
	m_lineSet = new SoLineSet;
    	m_coordsLineSet = new SoCoordinate3;
	
	SoLightModel *light = new SoLightModel;
	light->model = SoLightModel::BASE_COLOR;

	SoDrawStyle *drawStyle = new SoDrawStyle;
	drawStyle->lineWidth = 2;
	
	m_channelSep->addChild(m_scale);
	m_channelSep->addChild(m_trans);
	m_channelSep->addChild(m_rot);
	m_channelSep->addChild(m_mat);
	m_channelSep->addChild(m_coordsLineSet);
	m_channelSep->addChild(light);
	m_channelSep->addChild(drawStyle);
	m_channelSep->addChild(m_lineSet);

	CSearch * mySearch = new CSearch(configFile);
	switch (channelId)
	{
		case 'n':
		case 'N':
			{
				mySearch->get("NTimeAxis", m_timeAxis);
				mySearch->get("NAmplitudeAxis", m_amplitudeAxis);
				break;
			}
	case 'e':
	case 'E':
		{
			mySearch->get("ETimeAxis", m_timeAxis);
			mySearch->get("EAmplitudeAxis", m_amplitudeAxis);
			break;
		}
	case 'z':
	case 'Z':
		{
			mySearch->get("ZTimeAxis", m_timeAxis);
			mySearch->get("ZAmplitudeAxis", m_amplitudeAxis);
			break;
		}
	default:
		break;
	}
	
	m_counter = 0;
	m_stop = FALSE;
	//m_useSubSet = FALSE;
	m_holdFinal = TRUE;
	m_numofPointsRead = 0.0f;
	m_stretchAmplitude = 1;
	m_stretchTime = 1;

	delete mySearch;

}


CChannel::~CChannel()
{}

SoSeparator* CChannel::getChannelSep()
{
	return m_channelSep;
}

SoPointSet* CChannel::getPointSet()
{
	return m_pointSet;
}

SoLineSet* CChannel::getLineSet()
{
	return m_lineSet;
}

SoCoordinate3* CChannel::getCoordsPointSet()
{
	return m_coordsPointSet;
}

SoCoordinate3* CChannel::getCoordsLineSet()
{
	return m_coordsLineSet;
}


void CChannel::update()
{
	if (m_counter <= m_numofPointsRead)
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
				{
					p.set1Value(i,m_points[i][0], m_points[i][1], m_points[i][2]);
				}
			}
			else
			{
				if (m_counter < m_subSetNum)
				{
					if (m_wiggleDir == "FORWARD")
					{
						for (i = 0; i < m_counter; i++)
							p.set1Value(i,m_points[i][0], m_points[i][1], m_points[i][2]);
					}
					else
					{
						int i;
						float timeAxis = m_delta*m_counter;
						if (m_timeAxis == 'X' && m_amplitudeAxis == 'Y')
							for (i = 0; i < m_counter; i++,timeAxis-=m_delta)
								//p.set1Value(i,timeAxis, m_points[i][1]*m_stretchAmplitude,m_points[i][2]);
								p.set1Value(i,timeAxis, m_points[i][1],m_points[i][2]);
						if (m_timeAxis == 'Y' && m_amplitudeAxis == 'Z')
							for (i = 0; i < m_counter; i++,timeAxis-=m_delta)
								//p.set1Value(i,m_points[i][0],timeAxis,m_points[i][2]*m_stretchAmplitude);
								p.set1Value(i,m_points[i][0],timeAxis,m_points[i][2]);
						if (m_timeAxis == 'Z' && m_amplitudeAxis == 'X')
							for (i = 0; i < m_counter; i++,timeAxis-=m_delta)
								//p.set1Value(i,m_points[i][0]*m_stretchAmplitude,m_points[i][1],timeAxis);
								p.set1Value(i,m_points[i][0],m_points[i][1],timeAxis);
						if (m_timeAxis == 'Y' && m_amplitudeAxis == 'X')
							for (i = 0; i < m_counter; i++,timeAxis-=m_delta)
								//p.set1Value(i,m_points[i][0]*m_stretchAmplitude,-timeAxis,m_points[i][2]); // - timeAxis cos I want the wave to propagate down not up
								p.set1Value(i,m_points[i][0],-timeAxis,m_points[i][2]); // - timeAxis cos I want the wave to propagate down not up
					}
				}
				else
				{
					float timeAxis = 0.0f;
					// Show subset of points
					if (m_timeAxis == 'X' && m_amplitudeAxis == 'Y')
					{ 
						if (m_wiggleDir == "FORWARD")
							for (i = m_counter - m_subSetNum, j = 0; j < m_subSetNum; i++,j++,timeAxis+=m_delta)
								p.set1Value(j,timeAxis, m_points[i][1],m_points[i][2]);
						else
							for (i = m_counter - m_subSetNum, j = 0,timeAxis=m_delta*m_subSetNum; j < m_subSetNum; i++,j++,timeAxis-=m_delta)
							//	p.set1Value(j,timeAxis, m_points[i][1]*m_stretchAmplitude,m_points[i][2]);
								p.set1Value(j,timeAxis, m_points[i][1],m_points[i][2]);

					}
					if (m_timeAxis == 'Y' && m_amplitudeAxis == 'Z')
					{
						if (m_wiggleDir == "FORWARD")
							for (i = m_counter - m_subSetNum, j = 0; j < m_subSetNum; i++,j++,timeAxis+=m_delta)
								p.set1Value(j,m_points[i][0], timeAxis,m_points[i][2]);
						else
							for (i = m_counter - m_subSetNum, j = 0,timeAxis=m_delta*m_subSetNum; j < m_subSetNum; i++,j++,timeAxis-=m_delta)
							//	p.set1Value(j,m_points[i][0], timeAxis,m_points[i][2]*m_stretchAmplitude);
								p.set1Value(j,m_points[i][0], timeAxis,m_points[i][2]);
					}
					if (m_timeAxis == 'Z' && m_amplitudeAxis == 'X')
					{
						if (m_wiggleDir == "FORWARD")
							for (i = m_counter - m_subSetNum, j = 0; j < m_subSetNum; i++,j++,timeAxis+=m_delta)
								p.set1Value(j,m_points[i][0], m_points[i][1],timeAxis);
						else
							for (i = m_counter - m_subSetNum, j = 0,timeAxis=m_delta*m_subSetNum; j < m_subSetNum; i++,j++,timeAxis-=m_delta)
							//	p.set1Value(j,m_points[i][0]*m_stretchAmplitude, m_points[i][1],timeAxis);
								p.set1Value(j,m_points[i][0], m_points[i][1],timeAxis);
					}
					if (m_timeAxis == 'Y' && m_amplitudeAxis == 'X')
					{
						if (m_wiggleDir == "FORWARD")
							for (i = m_counter - m_subSetNum, j = 0; j < m_subSetNum; i++,j++,timeAxis+=m_delta)
								p.set1Value(j,m_points[i][0],timeAxis, m_points[i][2]);
						else
							for (i = m_counter - m_subSetNum, j = 0,timeAxis=m_delta*m_subSetNum; j < m_subSetNum; i++,j++,timeAxis-=m_delta)
							//	p.set1Value(j,m_points[i][0]*m_stretchAmplitude,-timeAxis, m_points[i][2]);
								p.set1Value(j,m_points[i][0],-timeAxis, m_points[i][2]);
					}

				}
			}
			m_coordsLineSet->point = p; 
			// scale and translate the channel depending on what is in p - Atul Nov 22
			float maxY = 0.0f;
			float minY = 0.0f;
			
			for ( i = 0; i < p.getNum(); i++)
			{
				SbVec3f aVec = p[i];
				//cout<<"After getting p[i] "<<i<<endl;
				if (m_amplitudeAxis=='X')
				{
					if (aVec[0] > maxY)
						maxY = aVec[0];
					if (aVec[0] < minY)
						minY = aVec[0];
				}	
				else
					if(m_amplitudeAxis == 'Z')
					{
						if (aVec[2] > maxY)
							maxY = aVec[2];
						if (aVec[2] < minY)
							minY = aVec[2];
					}
					else
						if (m_amplitudeAxis == 'Y')
						{
							if (aVec[1] > maxY)
								maxY = aVec[1];
							if (aVec[1] < minY)
								minY = aVec[1];
						}
			}
			float range = (maxY + minY)/2.0f;
			float scaleVal = 1.0f;
			
			if (fabsf(maxY) > fabsf(minY))
				scaleVal = fabsf(m_stretchAmplitude/maxY);
			//	scaleVal = fabsf(1.0/maxY);
			else
				scaleVal = fabsf(m_stretchAmplitude/minY);
			//	scaleVal = fabsf(1.0/minY);
		
			range *= m_stretchAmplitude;
			if (m_amplitudeAxis=='X')
			{
				m_trans->translation.setValue(-range, 0,0);
				m_scale->scaleFactor.setValue(scaleVal, 1,1);
				//cout<<"BHE scale "<<scaleVal<<endl;
			}
			if (m_amplitudeAxis == 'Z')
			{
				m_trans->translation.setValue(0,0,-range);
				//m_trans->translation.setValue(0,0,0);
				m_scale->scaleFactor.setValue(1,1,scaleVal);
				//cout<<"BHN scale "<<scaleVal<<endl;
			}
			if (m_amplitudeAxis == 'Y')
			{
				m_trans->translation.setValue(0,-range, 0);
				m_scale->scaleFactor.setValue(1,scaleVal, 1);
				//cout<<"BHZ scale "<<scaleVal<<endl;
			}
			SbVec3f scaleVec = m_scale->scaleFactor.getValue();
			if (m_timeAxis == 'X')
			{
				scaleVec[0] += m_stretchTime;
			}
			else
			if (m_timeAxis == 'Y')
			{
				scaleVec[1] += m_stretchTime;
			}
			else
			if (m_timeAxis == 'Z')
			{
				scaleVec[2] += m_stretchTime;
			}
			m_scale->scaleFactor = scaleVec;
			//m_scale->scaleFactor.setValue(scaleVec[0], scaleVal[1],scaleVal[2]);
//		}
	}
	else
	{

//		string outFileAbsName = "data.iv";
//		SoOutput out;
//		out.openFile(outFileAbsName.c_str());
//		SoWriteAction writeAction(&out);
//		writeAction.apply(m_channelSep); //write the entire scene graph to data.iv
//		out.closeFile();

		if (!m_holdFinal)
		{
			m_counter = 0;
			m_coordsLineSet->setToDefaults();
		}
		m_stop = TRUE;
	}
	
}

void CChannel::parseFile()
{

	// Open the file
	ifstream in(m_fileName.c_str());
	if (in.fail()) {
		cout << "File not found "<<m_fileName<<endl;
		return;
	}
	// inData will read in the data from the file
	// using inData cos you don't know how many data points are in the
	// file
	vector<float> inData;
	int counter = 1;	// to keep track of how many lines were counted
						// the first 30 lines are the cards
						// not data
	float maxY=0;		// calculating max and min - not used
	float minY=0;
	float scaleFactor;	// maxAmplitude(earlier scalefactor) will be maxY or abs(minY)
						// scaleFactor is the one in the file
						// TODO : use either - get rid of the other or rename it at least

	float xInterval;	// The xInterval is the first field
	// read full file
	while(!in.eof())
	{
		// Some data is on the first line
		// scaleFactor is the fourth field
		
		if(counter == 1)
		{
			float junk2, junk3, junk4;
			in >>xInterval>>junk2>>junk3>>scaleFactor>>junk4;
			m_delta = xInterval;
		}
		if (counter == 7)
		{
			float junk1, junk4, junk5;
			in >> junk1 >> m_latitude >> m_longitude >> junk4 >> junk5;
		}
		if (counter == 15)
		{
			float year, day, hour, mins, secs;
			in >> year>>day>>hour>>mins>>secs;
			//cout<<year<<day<<hour<<mins<<secs;
			m_startTime = (hour*60*60)+(mins*60)+secs;
		}

		if (counter == 23)
		{
			float junk;
			in >>m_stationName>>junk;
		}
		// ignore first 30 lines
		// TODO : possible error here if you try to read something not in first line
		//      : counter was not incremented in above loop
		if (counter < 31)
		{
			in.ignore(INT_MAX, '\n');
			counter++;
		}
		else
		{
			// data starts
			// 5 sample poinst are given 
			// get their average and treat that as the amplitude
			float y[5];
			float avgy;
			in >> y[0]>>y[1]>>y[2]>>y[3]>>y[4];
			avgy = (y[0] + y[1] + y[2] + y[3] + y[4])/5.0f;
			inData.push_back(avgy);
			// determine the maxY and minY - not used
			if (avgy > maxY)
				maxY = avgy;
			if (avgy < minY)
				minY = avgy;
			//cout<<" avgy " <<avgy<<" minY "<<minY<<" maxY "<<maxY<<endl;

		}
	}
	// counter variable for all the if loops below
	int i;

	// the scalefactor determined by getting maxY and minY
	// not used
	float maxAmplitude;
	if (maxY > abs(minY))
		maxAmplitude = maxY;
	else
		maxAmplitude = abs(minY);
	

	float range = (maxY - minY)/scaleFactor;
	//m_trans->translation.setValue((maxY- (range/2))

	// possible to scale amplitude here
	//for ( i = 0; i < inData.size(); i++)
	//	inData[i] = inData[i]/100;

	// have to allocate memory to m_points
	// depends on how many values were read into inData
	// initialize m_numofPointsRead too
	long rows = inData.size();
	m_numofPointsRead = inData.size();
    int cols = 3;
	m_points = new float*[rows]; // alocate rows memory
	float x = 0.0f; 
	float z = 0.0f;	
    for (i=0; i < rows; i++)	// each row has three coordinates
	{
        m_points[i] = new float[cols];
	}
	// now go ahead and populate m_points
	// TODO :the x coordinate is spaced out at 0.1 here
	//      :you should get the value from the first field in the file
	// You can scale the Y coordinates here also
	if (m_timeAxis == 'X' && m_amplitudeAxis == 'Y')
	{
		for (i=0; i < m_numofPointsRead; i++)
		{
			// Draw along X-Y plane : normal
			m_points[i][0] = x;
			m_points[i][1] = inData[i]/scaleFactor;
			m_points[i][2] = z;
			x+=xInterval; // so now using the first field 
		}
		float shift = (maxY/scaleFactor)- (range/2);
		m_trans->translation.setValue(0, -shift, 0);
	}

	if (m_timeAxis == 'Y' && m_amplitudeAxis == 'Z')
	{
		for (i=0; i < m_numofPointsRead; i++)
		{
			// Draw along Y-Z plane 
			m_points[i][1] = x;
			m_points[i][2] = inData[i]/scaleFactor;
			m_points[i][0] = z;
			x+=xInterval; // so now using the first field 
		}
		float shift = (maxY/scaleFactor)- (range/2);
		m_trans->translation.setValue(0, 0, -shift);
	}

	if (m_timeAxis == 'Z' && m_amplitudeAxis == 'X')
	{
		for (i=0; i < m_numofPointsRead; i++)
		{
			// Draw along X-Z plane : 
			m_points[i][2] = x;
			m_points[i][0] = inData[i]/scaleFactor;
			m_points[i][1] = z;
			x+=xInterval; // so now using the first field 
		}
		float shift = (maxY/scaleFactor)- (range/2);
		m_trans->translation.setValue(-shift, 0 , 0);
	}

		//x+=0.1; // time interval - could be useful for modification later
	

//		cout<<"x "<<m_points[i][0]<<" y "<<m_points[i][1]<<" z "<<m_points[i][2]<<endl;
	


	// Another place where you can scale the data

	switch (m_amplitudeAxis)
	{
		case 'X':
			{
			if (m_scaleType == "COMMON")
				m_scale->scaleFactor.setValue(1e04, 1, 1); //  X-Y plane
			if (m_scaleType == "GOOD_LOCAL")
				m_scale->scaleFactor.setValue(m_goodLocalScale, 1, 1); //  X-Y plane
			if (m_scaleType == "NORMALIZED_LOCAL")
				m_scale->scaleFactor.setValue(scaleFactor/maxAmplitude, 1, 1); //  X-Y plane
			break;
			}
		case 'Y':
			if (m_scaleType == "COMMON")
				m_scale->scaleFactor.setValue(1, 1e04, 1); //  X-Y plane
			if (m_scaleType == "GOOD_LOCAL")
				m_scale->scaleFactor.setValue(1, m_goodLocalScale, 1); //  X-Y plane
			if (m_scaleType == "NORMALIZED_LOCAL")
				m_scale->scaleFactor.setValue(1, scaleFactor/maxAmplitude, 1); //  X-Y plane
			break;
		case 'Z':
			if (m_scaleType == "COMMON")
				m_scale->scaleFactor.setValue(1,1, 1e04); // Y-Z plane
			if (m_scaleType == "GOOD_LOCAL")
				m_scale->scaleFactor.setValue(1,1, m_goodLocalScale); // Y-Z plane
			if (m_scaleType == "NORMALIZED_LOCAL")
				m_scale->scaleFactor.setValue(1,1, scaleFactor/maxAmplitude); // Y-Z plane
			break;
		default:
			break;
	}
	//m_scale->scaleFactor.setValue(1, 1e04, 1); //  X-Y plane
	
	//m_scale->scaleFactor.setValue(1e04,1, 1); // X-Z plane
	
	//m_scale->scaleFactor.setValue(1,1, 1e04); // Y-Z plane

	/*
	long rows = 5;
	m_numofPointsRead = rows;
    int cols = 3;
	m_points = new float*[rows];
	float x = 0.0f; 
	float y = 2.0f;
	float z = 0.0f;
	int i;
    for (i=0; i < rows; i++)
	{
        m_points[i] = new float[cols];
	}
	for (i=0; i < rows; i++)
	{
		m_points[i][0] = x;
		m_points[i][1] = y;
		m_points[i][2] = z;
		x+=5; // time interval - could be useful for modification later
		y+=3;

		cout<<"x "<<m_points[i][0]<<" y "<<m_points[i][1]<<" z "<<m_points[i][2]<<endl;
	}

*/

	/*
	// Use this if points are to be drawn
	
	float startX = 0.0f;
	long ctr = 0;
	for(i = 0; i < POINTSREAD; i++)
	{
		float between[50][3];
		SbVec3f s(xyz[i][0], xyz[i][1], xyz[i][2]);
		SbVec3f e(xyz[i+1][0], xyz[i+1][1], xyz[i+1][2]);
		cout<<"i " <<i <<endl;
		calculateIntermediatePts(between, s, e, startX);
		startX+=5;
		for (int j = 0; j < 50; j++, ctr++)
		{
			allxyz[ctr][0] = between[j][0];
			allxyz[ctr][1] = between[j][1];
			allxyz[ctr][2] = between[j][2];
			cout<<"ctr "<<ctr<<" j "<<j <<endl;
		}

	}
	*/
}

void CChannel::reset()
{
	m_counter = 0;
	m_coordsLineSet->setToDefaults();
	//m_stop = TRUE;
}

void CChannel::showAll()
{
	m_counter = m_numofPointsRead;
}

void CChannel::stop()
{
	m_stop = TRUE;
}

void CChannel::start()
{
	m_stop = FALSE;
	//m_counter = 0;
}

SbBool CChannel::isStopped()
{
	return m_stop;
}

void CChannel::setDiffuseColor(float r, float g, float b)
{
	m_mat->diffuseColor.setValue(r,g,b);
}

void CChannel::setRotation(char axis, float angle)
{
	SbVec3f X;
	SbVec3f Y;
	SbVec3f Z;
	X.setValue(1,0,0);
	Y.setValue(0,1,0);
	Z.setValue(0,0,1);
	
	SbMatrix newRotMatrix;
	
	SbMatrix rotMatrix;
	SbRotation r = m_rot->rotation.getValue();
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
	
	m_rot->rotation = rotMatrix;
}

float** CChannel::getPoints()
{
	return m_points;
}

long CChannel::getNumPointsRead()
{
	return m_numofPointsRead;
}

void CChannel::stretchTimeAxis(float val)
{
	m_stretchTime += val;
	/*
	SbVec3f scaleVec;
	scaleVec = m_scale->scaleFactor.getValue();
	switch (m_timeAxis)
	{
	case 'X':
		scaleVec[0] += val;
		break;
	case 'Y':
		scaleVec[1] += val;
		break;
	case 'Z':
		scaleVec[2] += val;
		break;
	default:
		break;
	}
	
	m_scale->scaleFactor.setValue(scaleVec);
	*/
}

void CChannel::stretchAmplitudeAxis(float val)
{
	m_stretchAmplitude *= val;

/*	SbVec3f scaleVec;
	scaleVec = m_scale->scaleFactor.getValue();
	switch (m_amplitudeAxis)
	{
	case 'X':
		scaleVec[0] *= val;
		break;
	case 'Y':
		scaleVec[1] *= val;
		break;
	case 'Z':
		scaleVec[2] *= val;
		break;
	default:
		break;
	}
	
	m_scale->scaleFactor.setValue(scaleVec);
	*/
}

float CChannel::getLatitude()
{
	return m_latitude;
}

float CChannel::getLongitude()
{
	return m_longitude;
}

float CChannel::getGoodLocalScale()
{
	return m_goodLocalScale;
}

SbVec3f CChannel::getScale()
{
	//SbVec3f scaleVec;
	//scaleVec = m_scale->scaleFactor.getValue();
	//return scaleVec;
	return m_scale->scaleFactor.getValue();
}

float CChannel::getStartTime()
{
	return m_startTime;
}

void CChannel::createSubSetPoints(float numPts)
{
	m_useSubSet = TRUE;
	m_subSetNum = numPts;

}

float CChannel::getDelta()
{
	return m_delta;
}

void CChannel::setWiggleDir(string wd)
{
	m_wiggleDir = wd;
}

void CChannel::next()
{
	m_counter++;
}

void CChannel::previous()
{
	m_counter--;
}

void CChannel::setStationName(string s)
{
	m_stationName = s;
}

string CChannel::getStationName()
{
	return m_stationName;
}

SbBool CChannel::isFinished()
{
	if (m_stop == TRUE && m_counter >= m_numofPointsRead)
		return TRUE;
	else
		return FALSE;
}

string CChannel::getChannelId()
{
	return m_channelId;
}

string CChannel::getStationId()
{
	return m_stationId;
}


void CChannel::addDataToChannel(string stationId, string siteId, string channelId , 
		float latitude, float longitude, float sampling, vector<int> pts)
{
	// m_stationName is the name ie. ANMO, SJG etc
	// m_stationId is Station1, Station2 etc
	m_stationName = stationId;
	m_siteId = siteId;
	m_channelId = channelId;
	m_latitude = latitude;
	m_longitude = longitude;
	m_delta = sampling;
	
	m_channelSep->setName(m_channelId.c_str());

	int i;
	// In real time throw away the old data
       for (int i = 0; i < pts.size(); i++)
       {
	   int tmp = pts[i];
	   m_pointsVec.push_back(tmp);
       }
	
	if (m_numofPointsRead > 0)
		delete m_points;
	//m_points = new float*[pts.size()];
	m_points = new float*[m_pointsVec.size()];
	//for (i = 0; i < pts.size(); i++)
	for (i = 0; i < m_pointsVec.size(); i++)
		m_points[i] = new float[3];

	float x=0.0f; float z=0.0f;
	float xInterval = m_delta; // TODO : Get exact value from data	
	//float scaleFactor = 1e+09;
	float scaleFactor = 1;
	float maxY = 0.0f;
	float minY = 0.0f;
	float range = 0.0f;

	//m_numofPointsRead = pts.size();
	m_numofPointsRead = m_pointsVec.size();

	if (m_timeAxis == 'X' && m_amplitudeAxis == 'Y')
	{
		for (i=0; i < m_numofPointsRead; i++)
		{
			// Draw along X-Y plane : normal
			m_points[i][0] = x;
			//m_points[i][1] = pts[i]/scaleFactor;
			m_points[i][1] = m_pointsVec[i]/scaleFactor;
			m_points[i][2] = z;
			x+=xInterval; // so now using the first field 
			/*if (pts[i]/scaleFactor > maxY)
				maxY = pts[i]/scaleFactor;
			if (pts[i]/scaleFactor < minY)
				minY = pts[i]/scaleFactor;
				*/
			if (m_pointsVec[i]/scaleFactor > maxY)
				maxY = m_pointsVec[i]/scaleFactor;
			if (m_pointsVec[i]/scaleFactor < minY)
				minY = m_pointsVec[i]/scaleFactor;
		}
		float maxAmplitude;
		if (abs(maxY) > abs(minY))
			maxAmplitude = abs(maxY);
		else
			maxAmplitude = abs(minY);
		range = (maxY - minY)/scaleFactor;
		float shift = (maxY/scaleFactor)- (range/2);
		m_trans->translation.setValue(-0.05, -shift, 0);
		//m_trans->translation.setValue(0, 0, 0);
	}

	if (m_timeAxis == 'Y' && m_amplitudeAxis == 'Z')
	{
		for (i=0; i < m_numofPointsRead; i++)
		{
			// Draw along Y-Z plane 
			m_points[i][1] = x;
			//m_points[i][2] = pts[i]/scaleFactor;
			m_points[i][2] = m_pointsVec[i]/scaleFactor;
			m_points[i][0] = z;
			x+=xInterval; // so now using the first field 
			/*if (pts[i]/scaleFactor > maxY)
				maxY = pts[i]/scaleFactor;
			if (pts[i]/scaleFactor < minY)
				minY = pts[i]/scaleFactor;
				*/
			if (m_pointsVec[i]/scaleFactor > maxY)
				maxY = m_pointsVec[i]/scaleFactor;
			if (m_pointsVec[i]/scaleFactor < minY)
				minY = m_pointsVec[i]/scaleFactor;
		}
		float maxAmplitude;
		if (abs(maxY) > abs(minY))
			maxAmplitude = abs(maxY);
		else
			maxAmplitude = abs(minY);
		range = (maxY - minY)/scaleFactor;
		float shift = (maxY/scaleFactor)- (range/2);
		m_trans->translation.setValue(0, -0.01, -shift);
		//m_trans->translation.setValue(0, 0, 0);
	}

	if (m_timeAxis == 'Z' && m_amplitudeAxis == 'X')
	{
		for (i=0; i < m_numofPointsRead; i++)
		{
			// Draw along X-Z plane : 
			m_points[i][2] = x;
			//m_points[i][0] = pts[i]/scaleFactor;
			m_points[i][0] = m_pointsVec[i]/scaleFactor;
			m_points[i][1] = z;
			x+=xInterval; // so now using the first field 
/*			if (pts[i]/scaleFactor > maxY)
				maxY = pts[i]/scaleFactor;
			if (pts[i]/scaleFactor < minY)
				minY = pts[i]/scaleFactor;
				*/
			if (pts[i]/scaleFactor > maxY)
			       maxY = m_pointsVec[i]/scaleFactor;
			if (pts[i]/scaleFactor < minY)
			       minY = m_pointsVec[i]/scaleFactor;
		}
		float maxAmplitude;
		if (abs(maxY) > abs(minY))
			maxAmplitude = abs(maxY);
		else
			maxAmplitude = abs(minY);
		range = (maxY - minY)/scaleFactor;
		float shift = (maxY/scaleFactor)- (range/2);
		m_trans->translation.setValue(-shift, 0 , -0.01);
		//m_trans->translation.setValue(0, 0, 0);
	}

	// Adding Nov 30
	if (m_timeAxis == 'Y' && m_amplitudeAxis == 'X')
	{
		for (i=0; i < m_numofPointsRead; i++)
		{
			// Draw along X-Y plane : 
			m_points[i][1] = x;
			//m_points[i][0] = pts[i]/scaleFactor;
			m_points[i][0] = m_pointsVec[i]/scaleFactor;
			m_points[i][2] = z;
			x+=xInterval; // so now using the first field 
			/*if (pts[i]/scaleFactor > maxY)
				maxY = pts[i]/scaleFactor;
			if (pts[i]/scaleFactor < minY)
				minY = pts[i]/scaleFactor;
				*/
			if (m_pointsVec[i]/scaleFactor > maxY)
				maxY = m_pointsVec[i]/scaleFactor;
			if (m_pointsVec[i]/scaleFactor < minY)
				minY = m_pointsVec[i]/scaleFactor;

		}
		float maxAmplitude;
		if (abs(maxY) > abs(minY))
			maxAmplitude = abs(maxY);
		else
			maxAmplitude = abs(minY);
		range = (maxY - minY)/scaleFactor;
		float shift = (maxY/scaleFactor)- (range/2);
		m_trans->translation.setValue(-shift, 0 , -0.01);
		//m_trans->translation.setValue(0, 0, 0);
	}


//	SoMFVec3f p;
/*	if (m_channelId == "BHE" || m_channelId == "BH1")
	{
		m_timeAxis = 'Z';
		m_amplitudeAxis = 'X';
		//for (i=0; i < m_numofPointsRead; i++)
		for (i=0; i < pts.size(); i++)
	        {
	         // Draw along X-Z plane : 
		         m_points[i][2] = x;
			 //m_points[i][0] = inData[i]/scaleFactor;
			 m_points[i][0] = pts[i]/scaleFactor;
			 m_points[i][1] = z;
			 x+=xInterval; // so now using the first field
			if (m_points[i][0] > maxY)
			       maxY = m_points[i][0];
			if (m_points[i][0] < minY)
				minY = m_points[i][0];	
			p.set1Value(i,m_points[i][0],m_points[i][1],m_delta*i);
	         }
		 range = (maxY - minY)/scaleFactor;
	         float shift = (maxY/scaleFactor)- (range/2);
		 m_trans->translation.setValue(-shift, 0 , 0);

	}
	else
		if (m_channelId == "BHN" || m_channelId == "BH2")
		{
			m_timeAxis = 'Y';
			m_amplitudeAxis = 'Z';

			//for (i=0; i < m_numofPointsRead; i++)
			for (i=0; i < pts.size(); i++)
	                {
	                // Draw along Y-Z plane 
		                 m_points[i][1] = x;
				 //m_points[i][2] = inData[i]/scaleFactor;
				 m_points[i][2] = pts[i]/scaleFactor;
				 m_points[i][0] = z;
				 x+=xInterval; // so now using the first field 
				if (m_points[i][2] > maxY)
			       		maxY = m_points[i][2];
				if (m_points[i][2] < minY)
					minY = m_points[i][2];	
				p.set1Value(i,m_points[i][0],m_points[i][1],m_delta*i);
			}
		 	range = (maxY - minY)/scaleFactor;
			float shift = (maxY/scaleFactor)- (range/2);
			m_trans->translation.setValue(0, 0, -shift);
		}
		else
			if (m_channelId == "BHZ")
			{
				m_timeAxis = 'X';
				m_amplitudeAxis = 'Y';
				//for (i=0; i < m_numofPointsRead; i++)
				for (i=0; i < pts.size(); i++)
		                {
		                  // Draw along X-Y plane : normal
		                     m_points[i][0] = x;
				     //m_points[i][1] = inData[i]/scaleFactor;
				     m_points[i][1] = pts[i]/scaleFactor;
				     m_points[i][2] = z;
				     x+=xInterval; // so now using the first field 
			       	     if (m_points[i][2] > maxY)
			       		maxY = m_points[i][2];
				     if (m_points[i][2] < minY)
					minY = m_points[i][2];	
			  	     p.set1Value(i,m_points[i][0],m_points[i][1],m_delta*i);
				}
		 		range = (maxY - minY)/scaleFactor;
				float shift = (maxY/scaleFactor)- (range/2);
				m_trans->translation.setValue(0, -shift, 0);
			}
*/
//	m_coordsLineSet->point = p;
//	float maxAmplitude;
//	if (maxY > abs(minY))
//		maxAmplitude = maxY;
//	else
//		maxAmplitude = abs(minY);
	// Another place where you can scale the data
	//m_scaleType = "NORMALIZED_LOCAL";	
	
		
}
