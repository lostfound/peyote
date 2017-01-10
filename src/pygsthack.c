/*
 *
 * Copyright (C) 2010-2011  Platon Peacel☮ve <platonny@ngs.ru>
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */
#include <Python.h>
#define NO_IMPORT_PYGOBJECT 1
#include <pygobject.h>
#include <gst/gst.h>

/*
 * Function to be called from Python
 */
static PyObject* py_child_proxy_get_child_by_index(PyObject* self, PyObject* args)
{
	GstObject *band;
	PyObject  *pycvolizer;
	GstElement *equalizer;
	PyObject* pyresult;
	int no;

	if(!PyArg_ParseTuple( args, "Oi:child_proxy_get_child_by_index", &pycvolizer, &no) ) return NULL;
	equalizer = pygobject_get(pycvolizer);

	band = gst_child_proxy_get_child_by_index (GST_CHILD_PROXY (equalizer), no);
	pyresult = (PyObject*) pygobject_new(band);
	g_object_unref( band );
	return pyresult;
}
/*
 * Bind Python function name to my C function
 */
static PyMethodDef myModule_methods[] = {
	{"child_proxy_get_child_by_index", (PyCFunction)py_child_proxy_get_child_by_index, METH_VARARGS},
	{NULL, NULL}
};

/*
 * Python calls this to let me initialize my module
 */
void initlibpygsthack(void)
{
	(void) Py_InitModule("libpygsthack", myModule_methods);
}

