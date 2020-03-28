#include "Python.h"
#if PY_MAJOR_VERSION >= 3
#define Num_FromLong PyLong_FromLong
#else
#define Num_FromLong PyInt_FromLong
#endif

#include <math.h>

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

static PyMethodDef TrMathMethods[] = {
    {"tr_float_to_int", trmath_tr_float_to_int, METH_VARARGS,
     "Cast floating point trace data to integer counts given the least-significant count value."},
    {NULL, NULL, 0, NULL}
};

PyMODINIT_FUNC
inittrmath(void)
{
    (void) Py_InitModule("trmath", TrMathMethods);
}
