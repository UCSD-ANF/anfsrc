/******************************************************************
 * ImmersaView
 * Copyright (C) 2002 Electronic Visualization Laboratory,
 * all rights reserved
 * By Atul Nayak, Chris Scharver, Vikas Chowdry, Andrew Johnson, Jason Leigh
 * University of Illinois at Chicago
 *
 * This publication and its text and code may not be copied for commercial
 * use without the express written permission of the University of Illinois
 * at Chicago.
 * The contributors disclaim any representation of warranty: use this
 * code at your own risk.
 * Direct questions, comments etc to cavern@evl.uic.edu
 ******************************************************************/
 
 /*********************************************************************

  Immersaview : An Open Inventor Viewer for the AGAVE/GeoWall
  
	ivutil.h :
	
	  This class provides common utility methods.
		
*********************************************************************/


#ifndef _IVUTIL_H
#define _IVUTIL_H

#pragma warning(disable:4275)
#pragma warning(disable:4251)

#include <Inventor/nodes/SoSeparator.h>
#include <Inventor/actions/SoWriteAction.h>
#include <Inventor/SoDB.h>         
#include <Inventor/SoInput.h>
#include <Inventor/nodes/SoSeparator.h>
#include <Inventor/fields/SoSFString.h> 
#include <Inventor/nodes/SoFile.h> 
#include <string>
using namespace std;
#define DTOR(r) ((r)*0.01745329f)
#define RTOD(r) ((r)*57.2957877f)

SoSeparator* loadFile(const char*);
string loadFileWithWildCardInPath(char*);
char* intoa(int);

float calcMagnitude(float* c);
 /*
{
        return(sqrt(c[0] * c[0] + c[1]*c[1] + c[2] * c[2]));   
}
*/
void normalize(float* c);
/*
 {
        float magnitude = calcMagnitude(c);   
        c[0] = c[0]/ magnitude;
    c[1] = c[1]/ magnitude;
    c[2] = c[2]/ magnitude;    
}
*/
// given 2 vectors calculate normal in res
void calcNormals(float* b1, float* b2, float* res);
/*
{
    res[0] = b1[1]*b2[2] - b2[1] * b1[2];
    res[1] = -(b1[0] * b2[2] - b2[0] * b1[2]);
    res[2] = b1[0]*b2[1] - b1[1]*b2[0];
}
*/
//given 2 vectors calculate angle
float calcAngle(float* b1, float* b2);
/*
{
        normalize(b1);
        normalize(b2);
        float dot = b1[0]*b2[0]+b1[1]*b2[1]+b1[2]*b2[2];
    cout <<"HI";
        float angle = acos(dot);
        return angle;
}
*/

void projectionBonA(float *A,float* B,float * projection);


#endif

