#ifndef _CSEISMOGRAM_HXX
#define _CSEISMOGRAM_HXX
#include "common.hxx"
#include <vector>
#include <map>
#include <string>
using namespace std;

class CSeismogram 
{
	public :
		CSeismogram();
		//CSeismogram(CSeismogram &);
		~CSeismogram();
		void setLatitude(float );
		void setLongitude(float );
		void setAmplitudeValues(vector<int> );
		void addAmplitudeValues(int*,int&);
		void setFrequency(float );
		float getLatitude();
		float getLongitude();
		float getFrequency();
		vector<int> getAmplitudeValues();
		SbBool haveNewData();
		void setHaveNewData(SbBool);
		//void operator = (CSeismogram&);

		string m_network;
		string m_station;
		string m_channel;
		//vector<int> m_pktCount;
	 	int m_nsamples;	
	protected :
		vector<int> m_amplitude;
		float 	    m_latitude;
		float 	    m_longitude;
		float       m_frequency;
		void init();
		SbBool m_haveNewData;

};

#endif
