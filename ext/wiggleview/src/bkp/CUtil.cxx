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

#include "CUtil.hxx"


#ifdef _WIN32
#include <iostream>
#include <string>
#include <fstream>
using namespace std;
#else
#include <iostream.h>
#include <string.h>
#include <fstream.h>
#endif

SoSeparator*
loadFile(const char* filename)
{
	SoInput myInput;
	if (!myInput.openFile(filename))
		return 0;
	if (!myInput.isValidFile())
	{
		cerr<<"File "<< filename <<"is not a valid Inventor file"<<endl;
		return NULL;
	}
//	else
//		cerr<<"Inventor Version used in File: "<<myInput.getIVVersion()<<endl;
	
	SoSeparator *geomObject = SoDB::readAll(&myInput);
	return geomObject;
}

// This function can be used with Windows or Linux currently
// not ported to Darwin
string
loadFileWithWildCardInPath(char* path)
{
#if (defined(WIN32) || defined(linux))
	string command;
	string p(path);
	//string p("jsutjunk");
#ifdef _WIN32
	command = "dir /B " + p + " > filelist.txt";
#else
	command = "ls " + p + " > filelist.txt";
#endif
	system(command.c_str());

	ifstream inFile("filelist.txt");

	//ofstream out("data.iv");
	//out<<"#Inventor V2.1 ascii"<<"/n";
	SoSeparator *root = new SoSeparator;
	root->ref();
	
	string fullPath;
	int n = p.find_first_of("*");
	if (n != -1)
		fullPath.assign(p.c_str(),n);
	else
	{
		fullPath.assign(p.c_str(), p.size());
#ifdef _WIN32
		fullPath.append("\\");
#else
		fullPath.append("//");
#endif
	}

	while(!inFile.eof())
	{
		string fileName;
		inFile >> fileName;
		if (fileName!= "")
		{
			string absoluteName = fullPath + fileName;

			//root->addChild(loadFile(absoluteName.c_str()));
			cerr<<"Fetching "<<absoluteName<<endl;
			SoSFString f;
			f.setValue(absoluteName.c_str());

			SoFile *aFile = new SoFile;
			aFile->name = f;
			
			root->addChild(aFile);
		}
	}

	//string outFileAbsName = fullPath + "data.iv";
	string outFileAbsName = "data.iv";
	SoOutput out;
	out.openFile(outFileAbsName.c_str());
	SoWriteAction writeAction(&out);
	writeAction.apply(root); //write the entire scene graph to data.iv
	out.closeFile();

	//return root;
	//return fullPath + "data.iv";
	return outFileAbsName;
#endif

#ifdef DARWIN
	return "UNKNOWN";
#endif

}

char* intoa(int num)
{
	int sign =0;
	static char buf[15];
	char *cp = buf+sizeof(buf)-1;
	if (num < 0)
	{
		sign = 1;
		num = -num;
	}
	do
	{
		*cp-- = '0' + num%10;
		num /= 10;
	} while (num);
	if (sign)
		*cp-- = '-';
	return (cp+1);
}

float calcMagnitude(float* c)

{
        return(sqrt(c[0] * c[0] + c[1]*c[1] + c[2] * c[2]));   
}

void normalize(float* c)
{
        float magnitude = calcMagnitude(c);   
        c[0] = c[0]/ magnitude;
    c[1] = c[1]/ magnitude;
    c[2] = c[2]/ magnitude;    
}

// given 2 vectors calculate normal in res
void calcNormals(float* b1, float* b2, float* res)
{
    res[0] = b1[1]*b2[2] - b2[1] * b1[2];
    res[1] = -(b1[0] * b2[2] - b2[0] * b1[2]);
    res[2] = b1[0]*b2[1] - b1[1]*b2[0];
}

//given 2 vectors calculate angle
float calcAngle(float* b1, float* b2)
{
        normalize(b1);
        normalize(b2);
        float dot = b1[0]*b2[0]+b1[1]*b2[1]+b1[2]*b2[2];
    cout <<"HI";
        float angle = acos(dot);
        return angle;
}

//: http://home.xnet.com/~fidler/triton/math/review/mat135/vector/dot/apps/proj-1.htm
void projectionBonA(float *A,float* B,float * projection)
{
	float dotAA = A[0]*A[0] + A[1]*A[1] + A[2]*A[2];
	float dotAB = A[0]*B[0] + A[1]*B[1] + A[2]*B[2];
	float factor = dotAB/dotAA;
	projection[0] = factor * A[0];
	projection[1] = factor * A[1];
	projection[2] = factor * A[2];
}