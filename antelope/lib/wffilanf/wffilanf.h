/* Copyright (c) 2007 Boulder Real Time Technologies, Inc. */
/* All rights reserved */

/* This software may be used freely in any way as long as
   the copyright statement above is not removed. */


/* Copyright (c) 2013-2014 The Regents of the University of California */

/*
 * wffilanf
 * ========
 *
 * This library contains three filters for use with BRTT Antelope:
 *
 * NOIS nois_min nois_max
 *     insert random noise into data with minimum amplitude noise_min and
 *     maximum amplitude nois_max
 *
 * SKEW twin
 *     apply skew averaging over time window twin seconds
 *
 * VAR twin
 *     apply var averaging over time window twin seconds
 */

#ifndef _wffilanf_h_
#define _wffilanf_h_

#include "tr.h" //This line may not be necessary
#include "stock.h"
#include "brttutil.h"

#define WFFILANF_TYPE_NOIS	1
#define WFFILANF_TYPE_SKEW	2
#define WFFILANF_TYPE_VAR	3

#define	SAMP(x,y)	(int)((x)<0.0?((x)/(y)-0.5):((x)/(y)+0.5)) //This is not yet necessary.

typedef struct wffilanf_def_ {
	int type;
	void *filter_stage;
	int sizeof_filter_stage;
	int (*filter) (int nsamps, double *tstart, double dt, float *data, void *filter_stage, int init, char *input_units, char *output_units);
} WffilanfDef;

typedef struct wffilanf_state_ {
	Tbl *stages;
	double tnext;
} WffilanfState;

/* Filtering functions */
int
wffilanf_nois_filter (int nsamp, double *tstart, double dt, float *data,
        void *filter_stage, int init, char *input_units, char *output_units);

int
wffilanf_skew_filter (int nsamp, double *tstart, double dt, float *data,
        void *filter_stage, int init, char *input_units, char *output_units);

int
wffilanf_var_filter (int nsamp, double *tstart, double dt, float *data,
        void *filter_stage, int init, char *input_units, char *output_units);


typedef struct wffilanf_stage_def {
	char *name;
	int type;
	int (*filter) (int nsamps, double *tstart, double dt, float *data, void *filter_stage, int init, char *input_units, char *output_units);
	int (*parse) (int argc, char **argv, WffilanfDef **filter_stage);
} WffilanfStageDef;

typedef struct wffilanf_nois_fil_ {
	int nois_min;	/*Noise range minimum*/
	int nois_max;	/*Noise range maximum*/
} WffilanfNoisFil;

//typedef struct wffilanf_skew {
//	float twin;	/*Time window*/
//} WffilanfSkewFil;
typedef struct wffilanf_skew_fil_ {
	double twin;	/* averaging time window */
	double toffset;	/* averaging window offset */
	double pcntok;	/* minimum percentage of good samples within averaging window */
	int ioff;	/* sample offset to beginning of filter for zero toffset */
	int n;		/* number of samples in filter */
	int nok;	/* minimum number of good samples in filter */
	int nsmps_size;	/* size of smps array in samples */
//	int nsmps;	/* number of previous data sample values */
	double tsmps;	/* time of first previous data sample value */
	float *smps;	/* previous data sample values */
} WffilanfSkewFil;

typedef struct wffilanf_var_fil_ {
	double twin;	/* averaging time window */
	double toffset;	/* averaging window offset */
	double pcntok;	/* minimum percentage of good samples within averaging window */
	int ioff;	/* sample offset to beginning of filter for zero toffset */
	int n;		/* number of samples in filter */
	int nok;	/* minimum number of good samples in filter */
	int nsmps_size;	/* size of smps array in samples */
//	int nsmps;	/* number of previous data sample values */
	double tsmps;	/* time of first previous data sample value */
	float *smps;	/* previous data sample values */
} WffilanfVarFil;

int
wffilanf_filter (void *userdata, char *filter_string, double gap_tolerance,
        int *nsamps, double *tstart, double *dt, float **data, int *data_size,
        char *input_units, char *output_units, Hook **state);




#endif
