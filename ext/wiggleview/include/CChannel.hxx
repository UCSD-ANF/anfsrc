#ifndef _CHANNEL_HXX
#define _CHANNEL_HXX

#include "common.hxx"
#include "CSearch.hxx"

class CChannel
{
public:

	CChannel(string, char);

	// give fileName
	CChannel(string);

	// Give the config file Name and the channel Id (e, n , z)
	CChannel(string, char, string);

	// Constructor for real time wiggleview
	// pass stationId, siteId, channelId,latitude, longitude
	// sampling , amplitude vector
	CChannel(string, string, string, float, float,float, vector<int>, string , char);

	~CChannel();

	void parseFile();

	void update();

	void reset();

	void next();

	void previous();

	void showAll();

	void stop();

	void start();

	SbBool isStopped();

	SoLineSet* getLineSet();

	SoPointSet* getPointSet();

	SoCoordinate3* getCoordsPointSet();

	SoCoordinate3* getCoordsLineSet();

	SoSeparator* getChannelSep();

	float** getPoints();

	long getNumPointsRead();

	void setDiffuseColor(float, float , float);

	void setRotation(char, float);

	void stretchTimeAxis(float);

	void stretchAmplitudeAxis(float);

	float getLatitude();

	float getLongitude();

	float getGoodLocalScale();

	float getDelta();

	SbVec3f getScale();

	float getStartTime();

	void createSubSetPoints(float);

	void setWiggleDir(string);

	string getStationName();

	SbBool isFinished();

	string getChannelId();

	string getStationId();
	
	void setStationName(string);

	void addDataToChannel(string, string, string, float, float,float, vector<int>);

	vector<int> m_pointsVec;
protected:

	//void init();

	string m_fileName;

	char m_timeAxis;
	
	char m_amplitudeAxis;
	
	float m_speed;
	
	long m_numofPointsRead;
	
	long m_numOfPointsInPointSet;

	long m_counter;

	string m_stationId;

	string m_stationName;

	// wrt
	string m_channelId;

	// wrt
	string m_siteId;

	float** m_points;

	float m_latitude;

	float m_longitude;

	float m_goodLocalScale;

	float m_stretchAmplitude;

	float m_stretchTime;

	string m_scaleType;

//	float m_points[5][3];

	SoPointSet *m_pointSet;

	SoLineSet *m_lineSet;

	SoCoordinate3 *m_coordsPointSet;

	SoCoordinate3 *m_coordsLineSet;

	SoSeparator *m_channelSep;

	SoScale *m_scale;

	SoTranslation *m_trans;

	SoRotation *m_rot;

	SoMaterial *m_mat;

	SbBool m_stop;

	float m_startTime;

	SbBool m_useSubSet;

	float m_subSetNum;

	float m_delta;

	string m_wiggleDir;

	SbBool m_holdFinal;

private :
	void init(string, char);
	
};

#endif
