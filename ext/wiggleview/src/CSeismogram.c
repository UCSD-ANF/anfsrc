#include <CSeismogram.hxx>

CSeismogram::CSeismogram()
{
    m_nsamples =0;
	
}

/*
CSeismogram::CSeismogram(CSeismogram& S)
{
	m_amplitude = S.m_amplitude;
	m_latitude  = S.m_latitude;
    m_longitude = S.m_longitude;
	m_frequency = S.m_frequency;
	m_haveNewData = S.m_haveNewData;
}

void CSeismogram::operator =(CSeismogram& S)
{
	m_amplitude = S.m_amplitude;
	m_latitude  = S.m_latitude;
    m_longitude = S.m_longitude;
	m_frequency = S.m_frequency;
	m_haveNewData = S.m_haveNewData;

}
*/
CSeismogram::~CSeismogram()
{}

void CSeismogram::setLatitude(float val)
{
    //cout<<"lat set to "<<m_latitude<<endl;
	m_latitude = val;
}

void CSeismogram::setLongitude(float val)
{
    //cout<<"lon set to "<<m_longitude<<endl;
	m_longitude = val;
}

void CSeismogram::setFrequency(float val)
{
	m_frequency = val;
}

void CSeismogram::setAmplitudeValues(vector<int> aVec)
{
	//int val;
	for (int i = 0; i < aVec.size(); i++)
	//{
		//val = aVec[i];
		m_amplitude.push_back(aVec[i]);
	//}
}

void CSeismogram::addAmplitudeValues(int * vals, int & num)
{
    // Check if there is more than 5 time slices of data
    // If yes then throw out the first slice of data
    // and add the new data
    //if (m_pktCount.size() == 5)
    //{
//	m_amplitude.erase(m_amplitude.begin(), m_amplitude.begin()+m_pktCount[0]
//		);
//	m_pktCount.erase(m_pktCount.begin());
//
  //  }
    m_nsamples = num;
    for (int i = 0; i < num; i++)
	m_amplitude.push_back(vals[i]);
    //m_pktCount.push_back(num);
}

float CSeismogram::getLatitude()
{
	return m_latitude;
}

float CSeismogram::getLongitude()
{
	return m_longitude;
}

float CSeismogram::getFrequency()
{
	return m_frequency;
}

vector<int> CSeismogram::getAmplitudeValues()
{
   vector<int> pts;
    int num = m_nsamples*0.01;
	for (int i = 0; i < num; i++)
	{
	    int tmp = m_amplitude[i];
	    pts.push_back(tmp);
	}
    	m_amplitude.erase(m_amplitude.begin(), m_amplitude.begin()+num);

    	cout <<"Return "<<0.01*m_nsamples<<" points "<<endl;
//	return m_amplitude;
	return pts;
}

SbBool CSeismogram::haveNewData()
{
	return m_haveNewData;
}

void CSeismogram::setHaveNewData(SbBool aFlag)
{
	m_haveNewData = aFlag;
}
