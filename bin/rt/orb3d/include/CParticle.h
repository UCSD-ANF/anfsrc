#ifndef _CPARTICLE_HXX
#define _CPARTICLE_HXX

#include "common.h"

class CParticle
{
public:

	CParticle();

	
	CParticle(float**, float**, float**, long,long,long);
	
	// Added May 15 2003
	CParticle(float**, float**, float**, long,long,long,
		double,double,double,double);

	~CParticle();

	// pass how many points to display
	void update(int);

	void reset();

	SoLineSet* getLineSet();

	SoPointSet* getPointSet();

	SoCoordinate3* getCoordsPointSet();

	SoCoordinate3* getCoordsLineSet();

	SoSeparator* getParticleSep();

	void setDiffuseColor(float, float , float);

	void setRotation(char, float);

	void increaseScale(float);
	
	void stop();

	void start();

	SbBool isStopped();

	void setGoodLocalScale(float );

	void setScale(SbVec3f);

	void setScale(SbVec3f, SbVec3f, SbVec3f);

	void setDelta(float);

	void createSubSetPoints(float);

	void next();

	void previous();

	// adding May 14, 03 
	SbVec3f getHeadTrans();


protected:

	float m_speed;

	long m_numofPointsRead;

	long m_numOfPointsInPointSet;

	long m_counter;

	float** m_points;

	SbBool m_stop;

	SoPointSet *m_pointSet;

	SoLineSet *m_lineSet;

	SoCoordinate3 *m_coordsPointSet;

	SoCoordinate3 *m_coordsLineSet;

	SoSeparator *m_particleSep;

	SoScale *m_scale;

	SoTranslation *m_trans;

	SoRotation *m_rot;

	SoMaterial *m_mat;

	float m_goodLocalScale;

	SbBool m_useSubSet;
	float m_subSetNum;
	float m_delta;

	SoTranslation *m_headTrans;

	SbBool m_holdFinal;
};

#endif
