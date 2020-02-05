#include "Python.h"
#if PY_MAJOR_VERSION >= 3
#define Num_FromLong PyLong_FromLong
#else
#define Num_FromLong PyInt_FromLong
#endif

#include <math.h>

struct module_state {
    PyObject *error;
};

#if PY_MAJOR_VERSION >= 3
#define GETSTATE(m) ((struct module_state*)PyModule_GetState(m))
#else
#define GETSTATE(m) (&_state)
static struct module_state _state;
#endif

static PyObject *
error_out(PyObject *m) {
    struct module_state *st = GETSTATE(m);
    PyErr_SetString(st->error, "something bad happened");
    return NULL;
}

static PyObject *
trmath_tr_float_to_int(PyObject *self, PyObject *args)
{
    PyObject* tr;
    PyObject* lsc;
    PyObject* temp;
    int trl;
    int i;

    if (!PyArg_ParseTuple(args, "O!O!", &PyList_Type, &tr,
                                        &PyFloat_Type, &lsc))
        return NULL;

    trl = PyList_Size(tr);

    for (i = 0; i < trl; i++ ){
        temp = PyNumber_TrueDivide(PyList_GetItem(tr, i), lsc);
        PyList_SetItem(tr, i, Num_FromLong((long) round(PyFloat_AsDouble(temp))));
        Py_DECREF(temp);
    }

    return Py_BuildValue("i", 1);

}

static PyMethodDef trmath_methods[] = {
    {"tr_float_to_int", trmath_tr_float_to_int, METH_VARARGS,
     "Cast floating point trace data to integer counts given the least-significant count value."},
    {NULL, NULL, 0, NULL}
};

#if PY_MAJOR_VERSION >= 3
static int trmath_traverse(PyObject *m, visitproc visit, void *arg) {
    Py_VISIT(GETSTATE(m)->error);
    return 0;
}

static int trmath_clear(PyObject *m) {
    Py_CLEAR(GETSTATE(m)->error);
    return 0;
}

static struct PyModuleDef moduledef = {
        PyModuleDef_HEAD_INIT,
        "trmath",
        NULL,
        sizeof(struct module_state),
        trmath_methods,
        NULL,
        trmath_traverse,
        trmath_clear,
        NULL
};

#define INITERROR return NULL

PyMODINIT_FUNC
PyInit_trmath(void)
#else
#define INITERROR return

void
inittrmath(void)
#endif
{
#if PY_MAJOR_VERSION >= 3
    PyObject *module = PyModule_Create(&moduledef);
#else
    PyObject *module = Py_InitModule("trmath", trmath_methods);
#endif

    if (module == NULL)
        INITERROR;
    struct module_state *st = GETSTATE(module);

    st->error = PyErr_NewException("trmath.Error", NULL, NULL);
    if (st->error == NULL) {
        Py_DECREF(module);
        INITERROR;
    }

#if PY_MAJOR_VERSION >= 3
    return module;
#endif
}
