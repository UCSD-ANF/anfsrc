#ifndef _CSEISMOMETER_HXX
#define _CSEISMOMETER_HXX

#include "common.h"
#include "CChannel.h"
#include "CParticle.h"
#include "CTimeTick.h"

class CSeismometer 
{
	public:
		
		CSeismometer();
		CSeismometer(string stationName, float lat, float lon, float elev_meters, float min_amplitude, float max_amplitude);
		~CSeismometer();
		//void update(SbTime,SbBool,int, SbBool); 

		SoSeparator* getSep();
		void stretchTimeAxis(float);
		void stretchAmplitudeAxis(float);
		void toggleWiggles();
		void toggleParticle();
		void start();
		void stop();
		void next();
		void previous();
		void reset();
		SbBool isFinished();
		string getStationName();
		void addDataToChannel(string channelId, int numPts, float xUnit,float sampRate, vector<float> pts, double currTime, double pktTime);
		void scrollTimeAxis(int shift);
		void updateTimeTick(SbTime currTime);
	protected:

		vector<CTimeTick*> m_timeTicks;
		CChannel *bhz;
		CChannel *bhn;
		CChannel *bhe;
		CParticle *particle;
		SoSeparator *m_seismometerSep;
		SoScale *m_scale;
		SoTranslation *m_trans;
		SoRotation *m_rot;
		SoMaterial *m_mat;
		SoSwitch *m_particleSwitch;
		SoSwitch *m_wiggleSwitch;
		float m_startTime;
		// Adding May 15 2003
		SbTime m_prevTime;
		float m_startTimeE;
		float m_startTimeN;
		float m_startTimeZ;
		// Finished adding May 15 2003

		SoText2 *m_stationText;
		string m_stationName;
		void init();

		// Store the coordinates of the line connecting the map and the
		// center of the grey sphere
		SoCoordinate3 *m_coordsLineSet;
		SoMFVec3f m_lollypoints;
		float m_lollystart[3];
		SoCoordinate3 *m_coordsLineToHead;

		float m_latitude;
		float m_longitude;
		float m_elev_meters;
		float m_min_amplitude;
		float m_max_amplitude;
};

#endif
