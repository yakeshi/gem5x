#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include "pybind11/embed.h"

#include "init.hh"
#include "python/embedded.hh"

namespace py = pybind11;

static PyObject *error;

static PyObject* _load(PyObject *self, PyObject *args) {
    PyObject *listObj;

    if (!PyArg_ParseTuple(args, "O!", &PyList_Type, &listObj)) {
        PyErr_SetString(error, "invalid arguments");
        return nullptr;
    }
    size_t num = PyList_Size(listObj);
    PyObject *elemObj;
    for (size_t i = 0; i < num; ++i) {
        elemObj = PyList_GetItem(listObj, i);
        auto utfNbytes = PyUnicode_AsEncodedString(elemObj, "utf-8", nullptr);
        char *modpath = PyBytes_AsString(utfNbytes);
        bool found = false;
        for (auto *embedded: gem5::EmbeddedPython::getList()) {
            if (strcmp(modpath, embedded->modpath) == 0) {
                if (!embedded->addModule()) {
                    PyErr_SetString(error, "add module failed");
                    return nullptr;
                }
                found = true;
            }
        }
        if (!found) {
            PyErr_SetString(error, "module not found");
            return nullptr;
        }
    }

    PyObject *sys_modules = PyImport_GetModuleDict();
    PyObject *_m5_obj = PyDict_GetItemString(sys_modules, "_m5");
    assert(_m5_obj != nullptr);
    py::module_ _m5 = py::reinterpret_borrow<py::module_>(_m5_obj);
    gem5::EmbeddedPyBind::initAll(_m5);
    return PyLong_FromLong(0);
}

static PyMethodDef CoresMethods[] = {
    {"load",  _load, METH_VARARGS,
     "load external ip cores module."},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};

static struct PyModuleDef cores_module = {
    PyModuleDef_HEAD_INIT,
    "cores",   /* name of module */
    nullptr, /* module documentation, may be NULL */
    -1,       /* size of per-interpreter state of the module,
                 or -1 if the module keeps state in global variables. */
    CoresMethods
};

PyMODINIT_FUNC PyInit_cores(void) {
    PyObject *m;

    m = PyModule_Create(&cores_module);
    if (m == nullptr)
        return nullptr;

    error = PyErr_NewException("cores.error", NULL, NULL);
    Py_XINCREF(error);
    if (PyModule_AddObject(m, "error", error) < 0) {
        Py_XDECREF(error);
        Py_CLEAR(error);
        Py_DECREF(m);
        return nullptr;
    }

    return m;
}
