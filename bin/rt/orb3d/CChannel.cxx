#include "CChannel.h"

CChannel::CChannel()
{
	init();
}

CChannel::CChannel(string channelId, float r, float g, float b)
{
  init();
  m_mat->diffuseColor.setValue(r,g,b);
  	m_channelSep->setName(m_channelId.c_str());
}


//CChannel::CChannel(string stationId, string siteId, string channelId , 
//		float latitude, float longitude, float sampling, vector<int> pts)
//CChannel::CChannel(string stationId, string siteId, string channelId, int num, int* pts)
//{
// 	// m_stationName is the name ie. ANMO, SJG etc
// 	// m_stationId is Station1, Station2 etc
// 	m_stationName = stationId;
// 	m_siteId = siteId;
// 	m_channelId = channelId;
// 	m_latitude = latitude;
// 	m_longitude = longitude;
// 	init();
// 	int i;
// 	m_points = new float*[pts.size()];
// 	for (i = 0; i < pts.size(); i++)
// 		m_points[i] = new float[3];

// 	float x=0.0f; float z=0.0f;
// 	float xInterval = 0.05f; // TODO : Get exact value from data	
// 	float scaleFactor = 1e+09;
// 	float maxY = 0.0f;
// 	float minY = 0.0f;
// 	float range = 0.0f;
// 	SoMFVec3f p;
// 	if (m_channelId == "" || m_channelId == "BH1")
// 	{
// 		m_timeAxis = 'Z';
// 		m_amplitudeAxis = 'X';
// 		//for (i=0; i < m_numofPointsRead; i++)
// 		for (i=0; i < pts.size(); i++)
// 	        {
// 	         // Draw along X-Z plane : 
// 		         m_points[i][2] = x;
// 			 //m_points[i][0] = inData[i]/scaleFactor;
// 			 m_points[i][0] = pts[i]/scaleFactor;
// 			 m_points[i][1] = z;
// 			 x+=xInterval; // so now using the first field
// 			if (m_points[i][0] > maxY)
// 			       maxY = m_points[i][0];
// 			if (m_points[i][0] < minY)
// 				minY = m_points[i][0];	
// 			p.set1Value(i,m_points[i][0],m_points[i][1],m_delta*i);
// 	         }
// 		 range = (maxY - minY)/scaleFactor;
// 	         float shift = (maxY/scaleFactor)- (range/2);
// 		 m_trans->translation.setValue(-shift, 0 , 0);

// 	}
// 	else
// 		if (m_channelId == "BHN" || m_channelId == "BH2")
// 		{
// 			m_timeAxis = 'Y';
// 			m_amplitudeAxis = 'Z';

// 			//for (i=0; i < m_numofPointsRead; i++)
// 			for (i=0; i < pts.size(); i++)
// 	                {
// 	                // Draw along Y-Z plane 
// 		                 m_points[i][1] = x;
// 				 //m_points[i][2] = inData[i]/scaleFactor;
// 				 m_points[i][2] = pts[i]/scaleFactor;
// 				 m_points[i][0] = z;
// 				 x+=xInterval; // so now using the first field 
// 				if (m_points[i][2] > maxY)
// 			       		maxY = m_points[i][2];
// 				if (m_points[i][2] < minY)
// 					minY = m_points[i][2];	
// 				p.set1Value(i,m_points[i][0],m_points[i][1],m_delta*i);
// 			}
// 		 	range = (maxY - minY)/scaleFactor;
// 			float shift = (maxY/scaleFactor)- (range/2);
// 			m_trans->translation.setValue(0, 0, -shift);
// 		}
// 		else
// 			if (m_channelId == "BHZ")
// 			{
// 				m_timeAxis = 'X';
// 				m_amplitudeAxis = 'Y';
// 				//for (i=0; i < m_numofPointsRead; i++)
// 				for (i=0; i < pts.size(); i++)
// 		                {
// 		                  // Draw along X-Y plane : normal
// 		                     m_points[i][0] = x;
// 				     //m_points[i][1] = inData[i]/scaleFactor;
// 				     m_points[i][1] = pts[i]/scaleFactor;
// 				     m_points[i][2] = z;
// 				     x+=xInterval; // so now using the first field 
// 			       	     if (m_points[i][2] > maxY)
// 			       		maxY = m_points[i][2];
// 				     if (m_points[i][2] < minY)
// 					minY = m_points[i][2];	
// 			  	     p.set1Value(i,m_points[i][0],m_points[i][1],m_delta*i);
// 				}
// 		 		range = (maxY - minY)/scaleFactor;
// 				float shift = (maxY/scaleFactor)- (range/2);
// 				m_trans->translation.setValue(0, -shift, 0);
// 			}

// 	m_coordsLineSet->point = p;
// 	float maxAmplitude;
// 	if (maxY > abs(minY))
// 		maxAmplitude = maxY;
// 	else
// 		maxAmplitude = abs(minY);
// 	// Another place where you can scale the data
// 	/*
// 	switch (m_amplitudeAxis)
// 	{
// 		case 'X':
// 		{
// 			if (m_scaleType == "COMMON")
// 				m_scale->scaleFactor.setValue(1e04, 1, 1); //  X-Y plane
// 			if (m_scaleType == "GOOD_LOCAL")
// 			        m_scale->scaleFactor.setValue(m_goodLocalScale, 1, 1); //  X-Y plane
// 			if (m_scaleType == "NORMALIZED_LOCAL")
// 			        m_scale->scaleFactor.setValue(scaleFactor/maxAmplitude, 1, 1); //  X-Y plane
// 			break;
// 		}
// 		case 'Y':
// 		{
// 			if (m_scaleType == "COMMON")
// 				m_scale->scaleFactor.setValue(1, 1e04, 1); //  X-Y plane
// 			if (m_scaleType == "GOOD_LOCAL")
// 			        m_scale->scaleFactor.setValue(1, m_goodLocalScale, 1); //  X-Y plane
// 		        if (m_scaleType == "NORMALIZED_LOCAL")
// 		                m_scale->scaleFactor.setValue(1, scaleFactor/maxAmplitude, 1); //  X-Y plane
// 		        break;
// 		}
// 		case 'Z':
// 		{
// 			if (m_scaleType == "COMMON")
// 		                m_scale->scaleFactor.setValue(1,1, 1e04); // Y-Z plane
// 		        if (m_scaleType == "GOOD_LOCAL")
// 		                m_scale->scaleFactor.setValue(1,1, m_goodLocalScale); // Y-Z plane
// 		        if (m_scaleType == "NORMALIZED_LOCAL")
// 			        m_scale->scaleFactor.setValue(1,1, scaleFactor/maxAmplitude); // Y-Z plane
// 		        break;
// 		}
// 		default:
// 			break;
// 	}
// 		*/
//}


void CChannel::init()
{
	m_channelSep = new SoSeparator;
	m_channelSep->ref();
	//m_scale = new SoScale;
	//m_trans = new SoTranslation;
	//m_rot   = new SoRotation;
	m_mat = new SoMaterial;
	//m_lineSet = new SoLineSet;
	SoDrawStyle *aDrawStyle = new SoDrawStyle;
        aDrawStyle->lineWidth = 2;
    	m_coordsLineSet = new SoCoordinate3;
	//SoLightModel *light = new SoLightModel;
	//light->model = SoLightModel::BASE_COLOR;
     
	//m_channelSep->addChild(m_scale);
	//m_channelSep->addChild(m_trans);
	//m_channelSep->addChild(m_rot);
	m_channelSep->addChild(m_mat);
	m_channelSep->addChild(aDrawStyle);
	m_channelSep->addChild(m_coordsLineSet);
	//m_channelSep->addChild(light);
	m_channelSep->addChild(new SoLineSet);

	for (int i =0 ; i < MAX_SAMPLES_DRAWN; i++)
		dataPts.push_back(0.0);
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


//void CChannel::update(int numOfPtsAdded)
//{
 //  //m_delta = m_xUnit;
//   if (m_counter < m_numofPointsRead)
//     {

//       if (!m_stop)
// 	//		{
// 	//m_counter++;; // later mod - add 10 lines each time
// 	m_counter += numOfPtsAdded;
//       if (m_counter > m_numofPointsRead)
// 	m_counter = m_numofPointsRead;

//       SoMFVec3f p;
//       int i, j;
//       if (m_useSubSet == FALSE)
// 	{
// 	  for (i = 0; i < m_counter; i++)
// 	    {
// 	      p.set1Value(i,m_points[i][0], m_points[i][1], m_points[i][2]);
// 	    }
// 	}
//       else
// 	{
// 	  if (m_counter < m_subSetNum)
// 	    {
// 	      if (m_wiggleDir == "FORWARD")
// 		{
// 		  for (i = 0; i < m_counter; i++)
// 		    p.set1Value(i,m_points[i][0], m_points[i][1], m_points[i][2]);
// 		}
// 	      else
// 		{
// 		  int i;
// 		  //float timeAxis = m_delta*m_counter;
// 		  float timeAxis = m_xUnit*m_counter;
// 		  if (m_timeAxis == 'X' && m_amplitudeAxis == 'Y')
// 		    //for (i = 0; i < m_counter; i++,timeAxis-=m_delta)
// 		    for (i = 0; i < m_counter; i++,timeAxis-=m_xUnit)
// 		      //p.set1Value(i,timeAxis, m_points[i][1],m_points[i][2]);
// 		      p.set1Value(i,timeAxis*1e02, m_points[i][1],m_points[i][2]);
// 		  if (m_timeAxis == 'Y' && m_amplitudeAxis == 'Z')
// 		    //for (i = 0; i < m_counter; i++,timeAxis-=m_delta)
// 		    for (i = 0; i < m_counter; i++,timeAxis-=m_xUnit)
// 		      //p.set1Value(i,m_points[i][0],timeAxis,m_points[i][2]);
// 		      p.set1Value(i,m_points[i][0],timeAxis*1e02,m_points[i][2]);
// 		  if (m_timeAxis == 'Z' && m_amplitudeAxis == 'X')
// 		    //for (i = 0; i < m_counter; i++,timeAxis-=m_delta)
// 		    for (i = 0; i < m_counter; i++,timeAxis-=m_xUnit)
// 		      //p.set1Value(i,m_points[i][0],m_points[i][1],timeAxis);
// 		      p.set1Value(i,m_points[i][0],m_points[i][1],timeAxis*1e02);
// 		  if (m_timeAxis == 'Y' && m_amplitudeAxis == 'X')
// 		    //for (i = 0; i < m_counter; i++,timeAxis-=m_delta)
// 		    for (i = 0; i < m_counter; i++,timeAxis-=m_xUnit)
// 		      //p.set1Value(i,m_points[i][0],-timeAxis,m_points[i][2]); // - timeAxis cos I want the wave to propagate down not up
// 		      p.set1Value(i,m_points[i][0],-timeAxis*1e02,m_points[i][2]); // - timeAxis cos I want the wave to propagate down not up

// 		}
// 	    }
// 	  else
// 	    {
// 	      float timeAxis = 0.0f;
// 	      // Show subset of points
// 	      if (m_timeAxis == 'X' && m_amplitudeAxis == 'Y')
// 		{ 
// 		  if (m_wiggleDir == "FORWARD")
// 		    //for (i = m_counter - m_subSetNum, j = 0; j < m_subSetNum; i++,j++,timeAxis+=m_delta)
// 		    for (i = m_counter - m_subSetNum, j = 0; j < m_subSetNum; i++,j++,timeAxis+=m_xUnit)
// 		      p.set1Value(j,timeAxis, m_points[i][1],m_points[i][2]);
// 		  else
// 		    //for (i = m_counter - m_subSetNum, j = 0,timeAxis=m_delta*m_subSetNum; j < m_subSetNum; i++,j++,timeAxis-=m_delta)
// 		    for (i = m_counter - m_subSetNum, j = 0,timeAxis=m_xUnit*m_subSetNum; j < m_subSetNum; i++,j++,timeAxis-=m_xUnit)
// 		      //p.set1Value(j,timeAxis, m_points[i][1],m_points[i][2]);
// 		      p.set1Value(j,timeAxis*1e02, m_points[i][1],m_points[i][2]);

// 		}
// 	      if (m_timeAxis == 'Y' && m_amplitudeAxis == 'Z')
// 		{
// 		  if (m_wiggleDir == "FORWARD")
// 		    //for (i = m_counter - m_subSetNum, j = 0; j < m_subSetNum; i++,j++,timeAxis+=m_delta)
// 		    for (i = m_counter - m_subSetNum, j = 0; j < m_subSetNum; i++,j++,timeAxis+=m_xUnit)
// 		      p.set1Value(j,m_points[i][0], timeAxis,m_points[i][2]);
// 		  else
// 		    //for (i = m_counter - m_subSetNum, j = 0,timeAxis=m_delta*m_subSetNum; j < m_subSetNum; i++,j++,timeAxis-=m_delta)
// 		    for (i = m_counter - m_subSetNum, j = 0,timeAxis=m_xUnit*m_subSetNum; j < m_subSetNum; i++,j++,timeAxis-=m_xUnit)
// 		      //p.set1Value(j,m_points[i][0], timeAxis,m_points[i][2]);
// 		      p.set1Value(j,m_points[i][0], timeAxis*1e02,m_points[i][2]);
// 		}
// 	      if (m_timeAxis == 'Z' && m_amplitudeAxis == 'X')
// 		{
// 		  if (m_wiggleDir == "FORWARD")
// 		    //for (i = m_counter - m_subSetNum, j = 0; j < m_subSetNum; i++,j++,timeAxis+=m_delta)
// 		    for (i = m_counter - m_subSetNum, j = 0; j < m_subSetNum; i++,j++,timeAxis+=m_xUnit)
// 		      p.set1Value(j,m_points[i][0], m_points[i][1],timeAxis);
// 		  else
// 		    //for (i = m_counter - m_subSetNum, j = 0,timeAxis=m_delta*m_subSetNum; j < m_subSetNum; i++,j++,timeAxis-=m_delta)
// 		    for (i = m_counter - m_subSetNum, j = 0,timeAxis=m_xUnit*m_subSetNum; j < m_subSetNum; i++,j++,timeAxis-=m_xUnit)
// 		      //p.set1Value(j,m_points[i][0], m_points[i][1],timeAxis);
// 		      p.set1Value(j,m_points[i][0], m_points[i][1],timeAxis*1e02);
// 		}
// 	      if (m_timeAxis == 'Y' && m_amplitudeAxis == 'X')
// 		{
// 		  if (m_wiggleDir == "FORWARD")
// 		    //for (i = m_counter - m_subSetNum, j = 0; j < m_subSetNum; i++,j++,timeAxis+=m_delta)
// 		    for (i = m_counter - m_subSetNum, j = 0; j < m_subSetNum; i++,j++,timeAxis+=m_xUnit)
// 		      p.set1Value(j,m_points[i][0],timeAxis, m_points[i][2]);
// 		  else
// 		    //for (i = m_counter - m_subSetNum, j = 0,timeAxis=m_delta*m_subSetNum; j < m_subSetNum; i++,j++,timeAxis-=m_delta)
// 		    for (i = m_counter - m_subSetNum, j = 0,timeAxis=m_xUnit*m_subSetNum; j < m_subSetNum; i++,j++,timeAxis-=m_xUnit)
// 		      //p.set1Value(j,m_points[i][0],-timeAxis, m_points[i][2]);
// 		      p.set1Value(j,m_points[i][0],-timeAxis*1e02, m_points[i][2]);
// 		}

// 	    }
// 	}
//       m_coordsLineSet->point = p;
//       string fName("updatePoints");
//       fName += m_timeAxis;
//       fName += m_amplitudeAxis;
//       fName += ".txt";
//       ofstream outFile(fName.c_str());
//       if (outFile.fail()) {
// 	cout << "Could not create File "<<fName<<endl;
// 	return;
//       }
//       for (i =0; i < p.getNum(); i++)
// 	outFile << p[i][0]<<" "<<p[i][1]<<" "<<p[i][2]<<endl;
//       outFile.close();
//       /*
// 	SbVec3f scaleVec = m_scale->scaleFactor.getValue();
			
// 	if (m_amplitudeAxis=='X')
// 	{
// 	scaleVec[0] *= m_stretchAmplitude;
// 	}
// 	if (m_amplitudeAxis == 'Z')
// 	{
// 	scaleVec[2] *= m_stretchAmplitude;
// 	}
// 	if (m_amplitudeAxis == 'Y')
// 	{
// 	scaleVec[1] *= m_stretchAmplitude;
// 	}
// 	if (m_timeAxis == 'X')
// 	{ 
// 	scaleVec[0] += m_stretchTime;
// 	}
// 	else
// 	if (m_timeAxis == 'Y')
// 	{
// 	scaleVec[1] += m_stretchTime;
// 	}
// 	else
// 	if (m_timeAxis == 'Z')
// 	{
// 	scaleVec[2] += m_stretchTime;
// 	}
// 	m_scale->scaleFactor = scaleVec;
// 	//m_scale->scaleFactor.setValue(scaleVec[0], scaleVal[1],scaleVal[2]);
// 	*/

//       //	}
//     }

//   else
//     {

//       //		string outFileAbsName = "data.iv";
//       //		SoOutput out;
//       //		out.openFile(outFileAbsName.c_str());
//       //		SoWriteAction writeAction(&out);
//       //		writeAction.apply(m_channelSep); //write the entire scene graph to data.iv
//       //		out.closeFile();

//       if (!m_holdFinal)
// 	{
// 	  m_counter = 0;
// 	  m_coordsLineSet->setToDefaults();
// 	}
//       m_stop = TRUE;
//     }
	
//}



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
	cout<<"Scale before stretching "<<scaleVec[0]<<" "<<scaleVec[1]<<" "
	<<scaleVec[2]<<endl;

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
	cout<<"Scale after stretching "<<scaleVec[0]<<" "<<scaleVec[1]<<" "
	<<scaleVec[2]<<endl;
	m_scale->scaleFactor.setValue(scaleVec);
	*/
}

void CChannel::stretchAmplitudeAxis(float val)
{
	m_stretchAmplitude *= val;
	/*
	SbVec3f scaleVec;
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



SbVec3f CChannel::getScale()
{
	SbVec3f scaleVec;
	scaleVec = m_scale->scaleFactor.getValue();
	return scaleVec;
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

// float CChannel::getDelta()
// {
// 	return m_delta;
// }

// void CChannel::setWiggleDir(string wd)
// {
// 	m_wiggleDir = wd;
// }

void CChannel::next()
{
	m_counter++;
}

void CChannel::previous()
{
	m_counter--;
}



SbBool CChannel::isFinished()
{
	if (m_stop == TRUE && m_counter >= m_numofPointsRead)
		return TRUE;
	else
		return FALSE;
}

// string CChannel::getChannelId()
// {
// 	return m_channelId;
// }




void CChannel::addDataToChannel(string channelId, int numPts, float xUnit, float sampleRate, vector<float> pts, double currTime, double pktTime)
{

  // Use MAX_SAMPLES_DRAWN to adjust the number of points drawn on the
  // annotation. Adjust m_xUnit so that the x axis adjusts for the increase or
  // decrease in points.
  // 400 is what usually fits into the annotation, using the m_xUnit obtained
  // from a packet.
  m_xUnit =  (xUnit * 400)/MAX_SAMPLES_DRAWN;
  //cout<<"m_xUnit is "<<m_xUnit<<endl;
  //getchar();
  float xVal= GLYPH_SCREEN_LEFT;
                                                                                                                                           
  cout<<"Number of points in dataPts before pushing "<< numPts <<" new points "<<dataPts.size()<<endl;
  SoMFVec3f p1;
  if (dataPts.size() >= MAX_SAMPLES_DRAWN)
    {
      //dataPts.erase(dataPts.begin(), dataPts.begin()+numPts);
      int j =0;
      int i;
      //for ( int i =0 ; i < numPts;i++)
//	{                                                 
//	  dataPts.push_back(pts[i]);
//	}
		int diff = (currTime - pktTime)* xUnit;
		cout<<"currTime "<<currTime<<"  - pktTime "<<pktTime<<":"<<currTime - pktTime<<endl;
		cout<<diff<<" points need to be erased"<<endl;
                //dataPts.erase(dataPts.end()-diff-numPts, dataPts.end()-diff);
                dataPts.erase(dataPts.begin(), dataPts.begin()+numPts);
  		cout<<"Number of points in dataPts after erasing "<< numPts <<" : "<<dataPts.size()<<endl;
                for (int i = 0; i < numPts; i++)
                        dataPts.insert(dataPts.end()-diff, pts[i]);
      //cout <<" i = "<<i<<endl;
      //getchar();
    }
  // else just draw. We haven't reached MAX_SAMPLES_DRAWN yet
  else
	{
    		//for (int i = 0; i < numPts; i++)
      		//	dataPts.push_back(pts[i]);
		cout<<"Datapts has less than "<<MAX_SAMPLES_DRAWN<<" points"<<endl;
		int diff = (currTime - pktTime)* xUnit;
		dataPts.erase(dataPts.begin()+diff+numPts, dataPts.begin()+diff);
		for (int i = 0; i < numPts; i++)
			dataPts.insert(dataPts.begin()+diff-i, pts[i]);
		
	}
  cout<<"Number of points in dataPts  after reading packet "<<dataPts.size()<<endl;
                                                          
  //SoMFVec3f p1;
  //for (int i = 0, xVal=GLYPH_SCREEN_LEFT;
  for (int i = 0;i < dataPts.size();i++)
    {
      xVal += m_xUnit;
      //cout<<"xVal is "<<xVal<<" ";
      p1.set1Value(i, xVal, dataPts[i], 0);
    }
  float m_max_amplitude = p1[0][1];
  float m_min_amplitude = p1[0][1];
  for (int i = 0 ; i < p1.getNum(); i++)
    {
      if (p1[i][1] > m_max_amplitude)
	m_max_amplitude = p1[i][1];
      if (p1[i][1] < m_min_amplitude)
	m_min_amplitude = p1[i][1];
    }
  cout<<"Number of points in p1 "<<p1.getNum()<<endl;
  
//	m_max_amplitude = 400.0;
//	m_min_amplitude = -400.0;                                                                                                                                         
  //float Ecenter;
  float m_centerAmplitude = (m_max_amplitude + m_min_amplitude)/2.;
  //float Eunit;
  float m_unitAmplitude = 0.5/(m_max_amplitude - m_min_amplitude);
    
  // For Annotation pts
 //  SoMFVec3f p2;
//   for (int i = 0; i < p1.getNum(); i++)
//     {
//       float plotPt;
//       plotPt = p1[i][1];
//       float diff;
//       diff = plotPt - m_centerAmplitude;
//       plotPt = (diff*m_unitAmplitude) + GLYPH_ESCREEN_CENTER;
//       p2.set1Value(i, p1[i][0], plotPt, 0);
//       //cout<<p2[i][0]<<","<<p2[i][1]<<" ";
//     }
//   cout<<"Number of points in p2 "<<p2.getNum()<<endl;

//   eCoords->point = p2;
  
                                                                                                                                         
  // Add coordinates for the component drawn at seismometer
  SoMFVec3f p3;
  xVal = 0.;
	/* The following lines of code draw the  data points 
	so that the earliest points are at the ground level*/
/*
  for (int i = 0; i < p1.getNum(); i++)
    {
      xVal += m_xUnit;
      float plotPt;
      plotPt = p1[i][1];
      float diff;
      diff = plotPt - m_centerAmplitude;
      plotPt = (diff*m_unitAmplitude);
      //p3.set1Value(i, plotPt,0, xVal);
      p3.set1Value(i, 0, xVal, plotPt);
      //cout<<p2[i][0]<<","<<p2[i][1]<<" ";
    }
  cout<<"Number of points in p3 "<<p3.getNum()<<endl;
  cout<<"p3[0][0] "<<p3[0][0]<<endl;
  //getchar();
  */
  for (int i = p1.getNum()-1; i >= 0; i--)
    {
      xVal += m_xUnit;
      float plotPt;
      plotPt = p1[i][1];
      float diff;
      diff = plotPt - m_centerAmplitude;
      plotPt = (diff*m_unitAmplitude);
      //p3.set1Value(i, plotPt,0, xVal);
	if (channelId == "BHN")
      		p3.set1Value(i, 0, xVal, plotPt);
	if (channelId == "BHE")
      		p3.set1Value(i, plotPt, xVal, 0);
      //cout<<p2[i][0]<<","<<p2[i][1]<<" ";
    }
  cout<<"Number of points in p3 "<<p3.getNum()<<endl;
  cout<<"p3[0][0] "<<p3[0][0]<<endl;
	
	m_coordsLineSet->point = p3;
                                                                                                                                           
}


void CChannel::convertDataToScreenPoints(vector<float> in,
											vector<float> &screenPts,
											const float screenCenter)
{
	for (int i = 0; i < in.size(); i++)
	{
		float plotPt;
		plotPt = in[i];
		float diff;
		diff = plotPt - m_centerAmplitude;
		plotPt = (diff*m_unitAmplitude*10) + screenCenter; // 10 factor randomly added
		screenPts.push_back(plotPt);
	}
}

void CChannel::scrollTimeAxis(int shift)
{
	//if (dataPts.size() >= MAX_SAMPLES_DRAWN)
		dataPts.erase(dataPts.begin(), dataPts.begin()+shift);
	//else
		for (int i = 0; i < shift; i++) {
			dataPts.push_back(0.0);
		}


}

void CChannel::setMinMaxAmplitude(float min, float max)
{
	m_min_amplitude = min;
	m_max_amplitude = max;
	
}
