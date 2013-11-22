/* Copyright (c) 2007 Boulder Real Time Technologies, Inc. */
/* All rights reserved */
 
/* This software may be used freely in any way as long as
   the copyright statement above is not removed. */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#include "tr.h" //This line may not be necessary
#include "stock.h"
#include "brttutil.h"

#define WFFILANF_TYPE_NOIS	1
#define WFFILANF_TYPE_SKEW	2

#define	SAMP(x,y)	(int)((x)<0.0?((x)/(y)-0.5):((x)/(y)+0.5)) //This line may not be necessary

static Arr *wffilanf_arr=NULL;

static Arr *wffilanf_stage_arr=NULL;

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

static int wffilanf_nois_filter (int nsamps, double *tstart, double dt, float *data, void *filter_stage, int init, char *input_units, char *output_units);
static int wffilanf_skew_filter (int nsamps, double *tstart, double dt, float *data, void *filter_stage, int init, char *input_units, char *output_units);

typedef struct wffilanf_stage_def {
	char *name;
	int type;
	int (*filter) (int nsamps, double *tstart, double dt, float *data, void *filter_stage, int init, char *input_units, char *output_units);
	int (*parse) (int argc, char **argv, WffilanfDef **filter_stage);
} WffilanfStageDef;

static int wffilanf_nois_parse (int argc, char **argv, WffilanfDef **filter_stage);
static int wffilanf_skew_parse (int argc, char **argv, WffilanfDef **filter_stage);

static WffilanfStageDef wffilanf_stages[] = {
	{"NOIS",		WFFILANF_TYPE_NOIS,	wffilanf_nois_filter, 		wffilanf_nois_parse},
	{"SKEW",		WFFILANF_TYPE_SKEW,	wffilanf_skew_filter, 		wffilanf_skew_parse},
};


typedef struct wffilanf_nois_fil_ {
	int nois_min;	/*Noise range minimum*/
	int nois_max;	/*Noise range maximum*/
} WffilanfNoisFil;

typedef struct wffilanf_skew {
	float twin;	/*Time window*/
} WffilanfSkewFil;

Tbl *wffilanf_define (void *userdata);
Tbl *wffilanf_parse (char *filter_string);
int wffilanf_filter (void *userdata, char *filter_string, double gap_tolerance,
		int *nsamps, double *tstart, double *dt, float **data, int *data_size,
		char *input_units, char *output_units, Hook **state);

static void 
wffilanfdef_free (void *userData)

{
	WffilanfDef *filterdef = userData;

	switch (filterdef->type){
	//Memory for any values referenced by pointers in filterdef->filter_stage should be freed here
	case WFFILANF_TYPE_NOIS:
	//WffilanfNoisFil contains no pointers
	case WFFILANF_TYPE_SKEW:
	//WffilanfSkewFil contains no pointers
	default:
		break;
	}
	free (filterdef);
}

/*This function is from the $ANTELOPE/example/c/wffilave example and
with only minor changes.*/
static int
wffilanf_setup_filters ()

{
	long i, n;

	if (wffilanf_stage_arr != NULL) return (0);

	wffilanf_stage_arr = newarr (0);
	if (wffilanf_stage_arr == NULL) {
		register_error (0, "wffilanf_setup_filters: newarr(wffilanf_stage_arr) error.\n");
		return (-1);
	}

	n = sizeof(wffilanf_stages)/sizeof(WffilanfStageDef);
	for (i=0; i<n; i++) {
		setarr (wffilanf_stage_arr, wffilanf_stages[i].name, &(wffilanf_stages[i]));
	}

	return (0);
}

/*This function is from the $ANTELOPE/example/c/wffilave example and
with only minor changes.*/
static void 
wffilanf_filter_stages_free (void *p)

{
	Tbl *filter_stages = p;

	if (p == NULL) return;

	freetbl (filter_stages, wffilanfdef_free);
}

static Tbl *
wffilanf_stages_copy (Tbl *filter_stages)

{
	Tbl *filter_stages_copy=NULL;
	int i;

	filter_stages_copy = newtbl (maxtbl(filter_stages));
	if (filter_stages_copy == NULL) {
		register_error (0, "wffilanf_stages_copy: newtbl(filter_stages_copy) error.\n");
		return (NULL);
	}
	for (i=0; i<maxtbl(filter_stages); i++) {
		WffilanfDef *filter_def;
		WffilanfDef *filter_def_copy;

		filter_def = (WffilanfDef *) gettbl (filter_stages, i);
		filter_def_copy = (WffilanfDef *) malloc (sizeof(WffilanfDef));
		if (filter_def_copy == NULL) {
			register_error (1, "wffilanf_stages_copy: malloc(filter_def_copy) error.\n");
			return (NULL);
		}
		*filter_def_copy = *filter_def;
		filter_def_copy->filter_stage = malloc (filter_def_copy->sizeof_filter_stage);
		if (filter_def_copy->filter_stage == NULL) {
			register_error (1, "wffilanf_stages_copy: malloc(filter_stage) error.\n");
			return (NULL);
		}
		memcpy (filter_def_copy->filter_stage,
				filter_def->filter_stage, filter_def_copy->sizeof_filter_stage);

		switch (filter_def_copy->type) {
		//A deep copy of any values referenced by pointers in filter_def->filter_stage should be created here
		case WFFILANF_TYPE_NOIS:
		//WffilanfNoisFil contains no pointers, no deep copies needed
		case WFFILANF_TYPE_SKEW:
		//WffilanfSkewFil contains no pointers, no deep copies needed
		default:
			break;
		}
	
		settbl (filter_stages_copy, i, filter_def_copy);
	}

	return (filter_stages_copy);
}

/*This function is from the $ANTELOPE/example/c/wffilave example and
with only minor changes.*/
static void
wffilanf_filter_state_free (void *vstate)

{
	WffilanfState *state = (WffilanfState *) vstate;

	if (state == NULL) return;
	wffilanf_filter_stages_free (state->stages);
	free (state);
}

/*This function is from the $ANTELOPE/example/c/wffilave example and
with only minor changes.*/
Tbl *
wffilanf_define (void *userdata)

{
	Tbl *defines;

	wffilanf_setup_filters();

	defines = keysarr (wffilanf_stage_arr);

	return (defines);
}

/*This function is from the $ANTELOPE/example/c/wffilave example
with only minor changes.*/
Tbl *
wffilanf_parse (char *filter_string)

{
	Tbl *filter_stages;
	int argcst, argc0;
	char **argvst, **argv0;
	int argc;
	char **argv;
	WffilanfDef *filter_stage;

	if (wffilanf_setup_filters() < 0) {
		register_error (0, "wffilanf_parse: wffilanf_setup_filters() error.\n");
		return (NULL);
	}

	if (splitlistc (filter_string, &argcst, &argvst, ";") < 0) {
		register_error (0, "wffilanf_parse: Unable to parse '%s'.\n", filter_string);
		return (NULL);
	}
	filter_stages = newtbl (1);
	if (filter_stages == NULL) {
		freeargs (argcst, argvst);
		register_error (0, "wffilanf_parse: newtbl(filter_stages) error.\n");
		return (NULL);
	}
	if (argcst < 1) {
		return (filter_stages);
	}
	for (argc0=argcst,argv0=argvst; argcst>0; argcst--,argvst++) {
		WffilanfStageDef *stage;

		if (splitlist (*argvst, &argc, &argv) < 0) {
			register_error (0, "wffilanf_parse: Unable to parse '%s'.\n", *argvst);
			freeargs (argc0, argv0);
			freetbl (filter_stages, wffilanfdef_free);
			return (NULL);
		}
		if (!strcmp(argv[0], "none")) {
			freeargs (argc, argv);
			continue;
		}

		stage = (WffilanfStageDef *) getarr (wffilanf_stage_arr, argv[0]);
		if (stage == NULL) {
			register_error (0, "wffilanf_parse: Cannot find stage definition for filter type '%s'.\n", argv[0]);
			freeargs (argc, argv);
			freeargs (argc0, argv0);
			freetbl (filter_stages, wffilanfdef_free);
			return (NULL);
		}

		if (stage->parse) {
			if ((*(stage->parse)) (argc, argv, &filter_stage) < 0) {
				register_error (0, "wffilanf_parse: Error parsing filter '%s'.\n", *argvst);
				freeargs (argc, argv);
				freeargs (argc0, argv0);
				freetbl (filter_stages, wffilanfdef_free);
				return (NULL);
			}
		} else {
			filter_stage = (WffilanfDef *) malloc(sizeof(WffilanfDef));
			if (filter_stage == NULL) {
				register_error (1, "wffilanf_parse: malloc(filter_stage) error.\n");
				freeargs (argc, argv);
				freeargs (argc0, argv0);
				freetbl (filter_stages, wffilanfdef_free);
				return (NULL);
			}
			memset (filter_stage, 0, sizeof(WffilanfDef));
			filter_stage->type = stage->type;
			filter_stage->filter = stage->filter;
		}
		settbl (filter_stages, -1, filter_stage);

		freeargs (argc, argv);
	}
	freeargs (argc0, argv0);

	return (filter_stages);
}

/*This function is from the $ANTELOPE/example/c/wffilave example
with only minor changes.*/
int
wffilanf_filter (void *userdata, char *filter_string, double gap_tolerance,
		int *nsamps, double *tstart, double *dt, float **data, int *data_size,
		char *input_units, char *output_units, Hook **state)

{
	Tbl *filter_stages=NULL;
	Tbl *filter_stages_copy;
	WffilanfState *filter_state=NULL;
	int init, k;

	if (filter_string == NULL) return (0);
	if (!strcmp(filter_string, "none")) return (0);

	init = 0;
	if (state == NULL || *state == NULL) {

		/* Lookup filter stages for this filter spec */

		if (wffilanf_arr == NULL) {
			wffilanf_arr = newarr (0);
			if (wffilanf_arr == NULL) {
				register_error (0, "wffilanf_filter: newarr(wffilanf_arr) error.\n");
				return (-1);
			}
		}
	
		filter_stages = getarr (wffilanf_arr, filter_string);
		if (filter_stages == NULL) {
			filter_stages = wffilanf_parse (filter_string);
			if (filter_stages == NULL) {
				register_error (0, "wffilanf_filter: wffilanf_parse(%s) error.\n", filter_string);
				return (-2);
			}
			setarr (wffilanf_arr, filter_string, filter_stages);
		}

		if (state) {
			filter_stages_copy = wffilanf_stages_copy (filter_stages);
			if (filter_stages_copy == NULL) {
				register_error (0, "wffilanf_filter: wffilanf_stages_copy(filter_stages_copy) error.\n");
				return (-1);
			}

			*state = new_hook (wffilanf_filter_state_free);
			if (*state == NULL) {
				register_error (0, "filter_filter: new_hook() error.\n");
				return (-1);
			}

			filter_state = (WffilanfState *) malloc (sizeof(WffilanfState));
			if (filter_state == NULL) {
				register_error (1, "wffilanf_filter: malloc(filter_state,%ld) error.\n", sizeof(WffilanfState));
				return (-1);
			}
			memset (filter_state, 0, sizeof(WffilanfState));

			filter_state->stages = filter_stages_copy;
			filter_state->tnext = -1.e30;

			(*state)->p = filter_state;
			filter_stages = filter_stages_copy;
		}
		init = 1;
	} else {
		filter_state = (*state)->p;
		filter_stages = filter_state->stages;
	}

	if (nsamps == NULL) return (0);
	if (*nsamps < 1) return (0);
	
	/* Loop over filter stages */

	for (k=0; k<maxtbl(filter_stages); k++) {
		WffilanfDef *filter_def;

		/* Make filter callback for this trace and stage */

		filter_def = (WffilanfDef *) gettbl (filter_stages, k);
		if (*(filter_def->filter) == NULL) continue;
		if ((*(filter_def->filter)) (*nsamps, tstart, *dt, *data, 
				filter_def->filter_stage, init, input_units, output_units) < 0) {
			register_error (0, "wffilanf_filter: filter_seg() error.\n");
			return (-1);
		}
	}

	return (0);
}

/*This function performs NOIS filtering*/

static int 
wffilanf_nois_filter (int nsamp, double *tstart, double dt, float *data, void *filter_stage, int init, 
							char *input_units, char *output_units)

{
	WffilanfNoisFil *fil = (WffilanfNoisFil *) filter_stage;
	int i, d, nois;
	float gap_value;

	/* input units are the same as output units */
        if (output_units) {
                if (input_units) strcpy (output_units, input_units);
                else strcpy (output_units, "-");
        }

	if (dt <= 0.0) return (0);

	if (nsamp < 1 || data == NULL) return (0);

	/* Grab a legitimate gap flag value */

	trfill_gap (&gap_value, 1);

	d = fil->nois_max - fil->nois_min + 1;

	srand(data[0]);

	for (i=0; i<nsamp; i++) {
		if (data[i] == gap_value) continue;

		nois = rand() % d;
		if(nois > fil->nois_max)
			nois = -(nois - fil->nois_max);

		data[i] = data[i] + (float)nois;
	}

	return (0);
}

/*This function performs SKEW filtering*/

static int 
wffilanf_skew_filter (int nsamp, double *tstart, double dt, float *data, void *filter_stage, int init, 
							char *input_units, char *output_units)

{
	WffilanfSkewFil *fil = (WffilanfSkewFil *) filter_stage;
	int i, j, hwlen, skc;
	float gap_value, dav, mu2, mu3;
	float data_out[nsamp];

	/* input units are the same as output units */
        if (output_units) 
                strcpy (output_units, "-");

	if (dt <= 0.0) return (0);

	if (nsamp < 1 || data == NULL) return (0);

	/* Grab a legitimate gap flag value */

	trfill_gap (&gap_value, 1);

	hwlen = (int)(fil->twin/(dt*2)); //calculate half window length in samples, implicit truncation rounds down to nearest integer

	for (i=0; i<nsamp; i++) {
		if (data[i] == gap_value) continue;
		dav = 0.0;
		mu2 = 0.0;
		mu3 = 0.0;
		skc = 0;
		if (i < hwlen){
			//rolling in
			skc = 0;
			for (j=0; j<=(i + hwlen); j++){
				if (data[j] == gap_value){
					skc++;
					continue;
				}
				dav += data[j];
			}
			dav = dav/(i + hwlen + 1 - skc);
			skc = 0;
			for (j=0; j<=i; j++){
				if (data[j] == gap_value){
					skc++;
					continue;
				}
				mu2 += pow((data[j] - dav), 2);
				mu3 += pow((data[j] - dav), 3);
			}
			mu2 = mu2/(i + hwlen + 1 - skc);
			mu3 = mu3/(i + hwlen + 1 - skc);
			data_out[i] = mu3/pow(mu2, 1.5);
		}
		else if (nsamp - i <= hwlen){
			//rolling out
			skc = 0;
			for (j=(i - hwlen); j<nsamp; j++){
				if (data[j] == gap_value){
					skc++;
					continue;
				}
				dav += data[j];
			}
			dav = dav/(hwlen + nsamp - i - skc);
			skc = 0;
			for (j=(i - hwlen); j<nsamp; j++){
				if (data[j] == gap_value){
					skc++;
					continue;
				}
				mu2 += pow((data[j] - dav), 2);
				mu3 += pow((data[j] - dav), 3);
			}
			mu2 = mu2/(hwlen + nsamp - i - skc);
			mu3 = mu3/(hwlen + nsamp - i - skc);
			data_out[i] = mu3/pow(mu2, 1.5);
		}
		else{
			//rolling along
			skc = 0;
			for (j=(i - hwlen); j<=(i + hwlen); j++){
				if (data[j] == gap_value){
					skc++;
					continue;
				}
				dav += data[j];
			}
			dav = dav/(2*hwlen + 1 - skc);
			skc = 0;
			for (j=(i - hwlen); j<=(i + hwlen); j++){
				if (data[j] == gap_value){
					skc++;
					continue;
				}
				mu2 += pow((data[j] - dav), 2);
				mu3 += pow((data[j] - dav), 3);
			}
			mu2 = mu2/(2*hwlen + 1 - skc);
			mu3 = mu3/(2*hwlen + 1 - skc);
			data_out[i] = mu3/pow(mu2, 1.5);
		}
	}

	for(i=0; i<nsamp; i++)
		data[i] = data_out[i];

	return (0);
}

/* This subroutine will parse the argument list derived from
   the filter_string for the NOIS parameters */

static int 
wffilanf_nois_parse (int argc, char **argv, WffilanfDef **filter_stage)

{
	int nois_min, nois_max;
	WffilanfNoisFil *fil;

	if (argc < 2) {
		register_error (0, "wffilanf_nois_parse: NOIS filter missing noise range minimum parameter.\n");
		return (-1);
	}
	nois_min = (int)atof(argv[1]);
	if (argc < 3) {
		register_error (0, "wffilanf_nois_parse: NOIS filter missing noise range maximum parameter.\n");
		return (-1);
	}
	nois_max = (int)atof(argv[2]);
	if (argc > 3) {
		register_error (0, "wffilanf_nois_parse: Too many parameters for NOIS filter.\n");
		return (-1);
	}

	fil = (WffilanfNoisFil *) malloc (sizeof(WffilanfNoisFil));
	if (fil == NULL) {
		register_error (1, "wffilanf_nois_parse: malloc(WffilanfNoisFil,%ld) error.\n", sizeof(WffilanfNoisFil));
		return (-1);
	}
	memset (fil, 0, sizeof(WffilanfNoisFil));
	fil->nois_min = nois_min;
	fil->nois_max = nois_max;
//	fil->type = WFFILANF_TYPE_NOIS;

	*filter_stage = (WffilanfDef *) malloc(sizeof(WffilanfDef));
	if (*filter_stage == NULL) {
		register_error (1, "wffilanf_nois_parse: malloc(filter_stage) error.\n");
		return (-1);
	}
	memset (*filter_stage, 0, sizeof(WffilanfDef));
	(*filter_stage)->type = WFFILANF_TYPE_NOIS;
	(*filter_stage)->filter_stage = fil;
	(*filter_stage)->sizeof_filter_stage = (int)sizeof(WffilanfNoisFil);
	(*filter_stage)->filter = wffilanf_nois_filter;

	return (0);
}

/* This subroutine will parse the argument list derived from
   the filter_string for the SKEW parameters */

static int 
wffilanf_skew_parse (int argc, char **argv, WffilanfDef **filter_stage)

{
	float twin;
	WffilanfSkewFil *fil;

	if (argc < 2) {
		register_error (0, "wffilanf_skew_parse: SKEW filter missing time window parameter.\n");
		return (-1);
	}
	twin = (float)atof(argv[1]);
	if (argc > 2) {
		register_error (0, "wffilanf_skew_parse: Too many parameters for SKEW filter.\n");
		return (-1);
	}

	fil = (WffilanfSkewFil *) malloc (sizeof(WffilanfSkewFil));
	if (fil == NULL) {
		register_error (1, "wffilanf_skew_parse: malloc(WffilanfSkewFil,%ld) error.\n", sizeof(WffilanfSkewFil));
		return (-1);
	}
	memset (fil, 0, sizeof(WffilanfSkewFil));
	fil->twin = twin;

	*filter_stage = (WffilanfDef *) malloc(sizeof(WffilanfDef));
	if (*filter_stage == NULL) {
		register_error (1, "wffilanf_skew_parse: malloc(filter_stage) error.\n");
		return (-1);
	}
	memset (*filter_stage, 0, sizeof(WffilanfDef));
	(*filter_stage)->type = WFFILANF_TYPE_SKEW;
	(*filter_stage)->filter_stage = fil;
	(*filter_stage)->sizeof_filter_stage = (int)sizeof(WffilanfSkewFil);
	(*filter_stage)->filter = wffilanf_skew_filter;

	return (0);
}
