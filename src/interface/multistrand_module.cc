/*
Multistrand nucleic acid kinetic simulator
Copyright (c) 2008-2023 California Institute of Technology. All rights reserved.
The Multistrand Team (help@multistrand.org)
*/

/*
 A simple extension module for python that exposes the
 SimulationSystem object as a createable object that has one method.
 */

#include "Python.h"
#include "structmember.h"

#include <iostream>
#include "ssystem.h"
#include "simoptions.h"
#include "options.h"

#include <time.h>
#include <string.h>
/* for strcmp */

#ifdef PROFILING
#include "google/profiler.h"
#include "google/heap-profiler.h"
#endif

typedef struct {
	PyObject_HEAD
	SimulationSystem *ob_system; /* Our one data member, no other attributes. */
	PyObject* options;
} SimSystemObject;

static PyObject *SimSystemObject_new(PyTypeObject *type, PyObject *args, PyObject *kwds) {

	SimSystemObject *self;

	self = (SimSystemObject *) type->tp_alloc(type, 0);
	/* uses the tp_alloc to create the right amount of memory - this is done since we allow sub-classes. */
	if (self != NULL) {
		self->ob_system = NULL;
		self->options = NULL;  // will be later set in _init ...
	}
	return (PyObject *) self;
}

static int SimSystemObject_init(SimSystemObject *self, PyObject *args) {
	if (!PyArg_ParseTuple(args, "O:SimSystem()", &self->options))
		return -1;

	/* Will be decreffed in Py_CLEAR(), or here if there's a type error. */
	Py_INCREF(self->options);

	/* check the type */
	if (strcmp(Py_TYPE(self->options)->tp_name, "Options") != 0) {
		printf("[%s] options name\n", Py_TYPE(self->options)->tp_name);
		/* Note that we'll need to change the above once it's packaged nicely. */
		Py_DECREF(self->options);
		PyErr_SetString(PyExc_TypeError, "Must be passed a single Options object.");
		return -1;
	}
	self->ob_system = new SimulationSystem(self->options);
	if (self->ob_system == NULL) /* something horrible occurred */
	{
		Py_DECREF(self->options);
		PyErr_SetString(PyExc_MemoryError,
						"Could not create the SimulationSystem [C++] object, possibly memory issues?.");
		return -1;
	}
	return 0;
}

static PyObject *SimSystemObject_start(SimSystemObject *self, PyObject *args) {
	if (!PyArg_ParseTuple(args, ":start"))
		return NULL;

	if (self->ob_system == NULL) {
		PyErr_SetString(PyExc_AttributeError,
						"The associated SimulationSystem [C++] object no longer exists, cannot start the system.");
		return NULL;
	}
	self->ob_system->StartSimulation();

	Py_RETURN_NONE;
}

static PyObject *SimSystemObject_initialInfo(SimSystemObject *self, PyObject *args) {
	if (!PyArg_ParseTuple(args, ":initialInfo"))
		return NULL;

	if (self->ob_system == NULL) {
		PyErr_SetString(PyExc_AttributeError,
						"The associated SimulationSystem [C++] object no longer exists, cannot query the system.");
		return NULL;
	}
	self->ob_system->initialInfo();

	Py_RETURN_NONE;
}

static PyObject *SimSystemObject_localTransitions(SimSystemObject *self, PyObject *args) {
	if (!PyArg_ParseTuple(args, ":localTransitions"))
		return NULL;

	if (self->ob_system == NULL) {
		PyErr_SetString(PyExc_AttributeError,
						"The associated SimulationSystem [C++] object no longer exists, cannot query the system.");
		return NULL;
	}
	self->ob_system->localTransitions();

	Py_RETURN_NONE;
}

static int SimSystemObject_traverse(SimSystemObject *self, visitproc visit, void *arg) {
	Py_VISIT(self->options);
	return 0;
}

static int SimSystemObject_clear(SimSystemObject *self) {
	Py_CLEAR(self->options);
	return 0;
}

static void SimSystemObject_dealloc(SimSystemObject *self) {
	PyObject_GC_UnTrack(self);

	if (self->ob_system != NULL) {
		delete self->ob_system;
		self->ob_system = NULL;
	}

	SimSystemObject_clear(self);

	Py_TYPE(self)->tp_free((PyObject *) self);
}

const char docstring_SimSystem[] =
		"\
Python Wrapper for Multistrand's C++ SimulationSystem object.\n\
\n\
Provides a very very simple interface to the StartSimulation method, to \n\
actually run the simulation. Otherwise fairly boring.\n";

const char docstring_SimSystem_start[] =
		"\
SimSystem.start( self )\n\
\n\
Start the simulation; only returns when the simulation has been completed. \n\
Information is only returned from the simulation via the Options object it \n\
was created with.\n";

const char docstring_SimSystem_initialInfo[] = "\
SimSystem.initialInfo( self )\n\
\n\
Query information about the initial state. \n";

const char docstring_SimSystem_localTransitions[] =
		"\
SimSystem.localTransitions( self )\n\
\n\
Given the initial state, traverses into each transition once. \n";

const char docstring_SimSystem_init[] =
		"\
:meth:`multistrand.system.SimSystem.__init__( self, *args )`\n\
\n\
Initialization of SimSystem object:\n\
\n\
Arguments:\n\
options [type=:class:`multistrand.options.Options`]  -- The options to use for\n\
                                                        this simulation. Is a\n\
                                                        required argument.\n\
\n";

static PyMethodDef SimSystemObject_methods[] = {
  { "__init__", (PyCFunction) SimSystemObject_init,
  	METH_COEXIST | METH_VARARGS, PyDoc_STR(docstring_SimSystem_init) },
  { "start", (PyCFunction) SimSystemObject_start,
  	METH_VARARGS, PyDoc_STR(docstring_SimSystem_start) },
  { "initialInfo", (PyCFunction) SimSystemObject_initialInfo,
  	METH_VARARGS, PyDoc_STR(docstring_SimSystem_initialInfo) },
  { "localTransitions", (PyCFunction) SimSystemObject_localTransitions,
  	METH_VARARGS, PyDoc_STR(docstring_SimSystem_localTransitions) },
  { NULL, NULL } /* Sentinel */
  /* Note that the dealloc, etc methods are not
  defined here, they're in the type object's
  methods table, not the basic methods table. */
};

static PyMemberDef SimSystemObject_members[] = {
	{ "options", T_OBJECT_EX, offsetof(SimSystemObject, options), 0,
	  "The :class:`multistrand.options.Options` object controlling this simulation system." },
	{ NULL } /* Sentinel */
};

static PyTypeObject SimSystem_Type = {
   /* Note that the ob_type field cannot be initialized here. */
   PyVarObject_HEAD_INIT(NULL, 0)
   .tp_name = "multistrand.system.SimSystem",
   .tp_basicsize = sizeof(SimSystemObject),
   .tp_itemsize = 0, /* [it's something that's a relic, should be 0] */
   /* standard method defs are next */
   .tp_dealloc = (destructor) SimSystemObject_dealloc,
   .tp_vectorcall_offset = 0, /* new slot semantics in Python 3.8 */
   .tp_getattr = 0, .tp_setattr = 0,
   .tp_as_async = 0, /* new slot semantics in Python 3.8 */
   .tp_repr = 0, .tp_as_number = 0, .tp_as_sequence = 0, .tp_as_mapping = 0,
   .tp_hash = 0, .tp_call = 0, .tp_str = 0, .tp_getattro = 0, .tp_setattro = 0,
   .tp_as_buffer = 0,
   .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE | Py_TPFLAGS_HAVE_GC,
   .tp_doc = PyDoc_STR(docstring_SimSystem),
   .tp_traverse = (traverseproc) SimSystemObject_traverse,
   .tp_clear = (inquiry) SimSystemObject_clear,
   .tp_richcompare = 0, .tp_weaklistoffset = 0, .tp_iter = 0, .tp_iternext = 0,
   .tp_methods = SimSystemObject_methods,
   .tp_members = SimSystemObject_members,
   .tp_getset = 0, .tp_base = 0, .tp_dict = 0,
   .tp_descr_get = 0, .tp_descr_set = 0, .tp_dictoffset = 0,
   .tp_init = (initproc) SimSystemObject_init,
   .tp_alloc = 0,
   .tp_new = (newfunc) SimSystemObject_new,
   .tp_free = 0, .tp_is_gc = 0,
};

static PyObject *System_initialize_energymodel(PyObject *self, PyObject *args) {
	PyObject *options_object = NULL;

	if (!PyArg_ParseTuple(args, "|O:initialize_energy_model( [options])", &options_object))
		return NULL;

	EnergyModel *temp = Loop::GetEnergyModel();

	if (temp != NULL)
		delete temp;
	if (options_object == NULL || options_object == Py_None)
		Loop::SetEnergyModel( NULL);
	else {
		temp = NULL;
		if (testLongAttr(options_object, parameter_type, =, 0))
			throw std::invalid_argument("Attempting to load ViennaRNA parameters (depreciated)");
		//temp = new ViennaEnergyModel( options_object );
		else
			temp = new NupackEnergyModel(options_object);
		Loop::SetEnergyModel(temp);
	}
	Py_RETURN_NONE;
}

static PyObject *System_calculate_energy(PyObject *self, PyObject *args) {

	SimulationSystem *temp = NULL;
	PyObject *options_object = NULL;
	PyObject *start_state_object = NULL;
	PyObject *energy;
	int typeflag = 0;
	if (!PyArg_ParseTuple(args, "O|Oi:energy(state, options[, energytypeflag])",
						  &start_state_object, &options_object, &typeflag))
		return NULL;
	if (!(0 <= typeflag && typeflag <= 3)) {
		PyErr_SetString(PyExc_TypeError, "Invalid 'energy_type' argument!");
		return NULL;
	}
	if (options_object != NULL) {

		temp = new SimulationSystem(options_object);

	} else {
		temp = new SimulationSystem();

		if (temp->isEnergymodelNull()) {
			PyErr_Format(
				PyExc_AttributeError,
				"No energy model available, cannot compute energy. Please pass an options object, or use multistrand.system.initialize_energy_model(...).\n");
			return NULL;
		}
	}
	energy = temp->calculateEnergy(start_state_object, typeflag);
	delete temp;
	return energy;
}

static PyObject *System_calculate_rate(PyObject *self, PyObject *args, PyObject *keywds) {
	PyObject *options_object = NULL;
	PyObject *rate;
	double drate = -1.0;
	double start_energy, end_energy;
	int joinflag = 0;
	EnergyModel *em = NULL;

	static char *kwlist[] = { "start_energy", "end_energy", "options", "joinflag", NULL };

	if (!PyArg_ParseTupleAndKeywords(
			args, keywds,
			"dd|Oi:calculate_rate(start_energy, end_energy, [options=None, joinflag=0])",
			kwlist, &start_energy, &end_energy, &options_object, &joinflag))
		return NULL;

	if (options_object == NULL) {
		em = Loop::GetEnergyModel();
		if (em == NULL) {
			PyErr_Format(
				PyExc_AttributeError,
				"No energy model available, cannot compute rates. Please pass an options object, or use multistrand.system.initialize_energy_model(...).\n");
			return NULL;
		}

	} else if (options_object != NULL) {
		if (testLongAttr(options_object, parameter_type, =, 0)) {
			throw std::invalid_argument(
				"Attempting to load ViennaRNA parameters (depreciated)");
//        em = new ViennaEnergyModel( options_object );
		} else {
			em = new NupackEnergyModel(options_object);
		}

		if (em == NULL) {
			PyErr_Format(
				PyExc_AttributeError,
				"Could not initialize the energy model, cannot compute rates. Please pass a valid options object, or use multistrand.system.initialize_energy_model(...).\n");

			return NULL;
		}
		if (Loop::GetEnergyModel() == NULL) {
			Loop::SetEnergyModel(em);
		}
	}

	if (joinflag == 1) // join
		drate = em->getJoinRate();
	else if (joinflag == 2) // break
		drate = em->returnRate(start_energy, end_energy, 3);
	else
		drate = em->returnRate(start_energy, end_energy, 0);

	rate = PyFloat_FromDouble(drate);

	if (em != Loop::GetEnergyModel())
		delete em;

	return rate;
}

static PyObject *System_run_system(PyObject *self, PyObject *args) {
#ifdef PROFILING
	HeapProfilerStart("ssystem_run_system.heap");
#endif

	SimulationSystem *temp = NULL;
	PyObject *options_object = NULL;
	if (!PyArg_ParseTuple(args, "O|Oi:run_system( options )", &options_object))
		return NULL;
	Py_INCREF(options_object);

	temp = new SimulationSystem(options_object);
	temp->StartSimulation();

	delete temp;
	temp = NULL;

#ifdef PROFILING
	HeapProfilerDump("run_system");
	HeapProfilerStop();
#endif

	Py_XDECREF(options_object);
	Py_RETURN_NONE;
}

static PyMethodDef System_methods[] = {
	{ "energy", (PyCFunction) System_calculate_energy,
	  METH_VARARGS, PyDoc_STR(" \
energy( start_state, options=None, energy_type=0)\n\
Computes the energy of the passed state [a list of complexes], using \
temperature, etc, settings from the options object passed.\n\n\
Parameters\n\
energy_type = options.Energy_Type.Loop_energy    : [default] no volume or association terms included. So only loop energies remain.\n\
energy_type = options.Energy_Type.Volume_energy  : include dG_volume. No clear interpretation for this.\n\
energy_type = options.Energy_Type.Complex_energy : include dG_assoc. This is the NUPACK complex microstate energy, sans symmetry terms.\n\
energy_type = options.Energy_Type.Tube_energy    : include dG_volume + dG_assoc. Summed over complexes, this is the system state energy.\n\
\n\
options = None [default]: Use the already initialized energy model.\n\
options = ...: If not none, should be a multistrand.options.Options object, which will be used for initializing the energy model ONLY if there is not one already present.\n")
	},
	{ "calculate_rate", (PyCFunction) System_calculate_rate,
	  METH_VARARGS | METH_KEYWORDS, PyDoc_STR(" \
calculate_rate(start_energy, end_energy, options=None, joinflag=0)\n\
Computes the rate of transition for the current kinetics model.\n\
\n\
Parameters\n\
start_energy, end_energy: Energies should always be WITHOUT dG_assoc and dG_volume.\n\
\n\
options = None [default]: Use the already initialized energy model.\n\
options = ...: If not none, should be a multistrand.options.Options object, which will be used for the energy model. Sets the default energy model for later calls ONLY if there is not one already present.\n\
\n\
joinflag = 0 [default]: unimolecular transition\n\
joinflag = 1: bimolecular join, passed energies are not relevant\n\
joinflag = 2: bimolecular break, energies are relevant\n")
	},
	{ "initialize_energy_model", (PyCFunction) System_initialize_energymodel,
	  METH_VARARGS, PyDoc_STR(" \
initialize_energy_model( options = None )\n\
Initialize the Multistrand module's energy model using the options object given. If a model already exists, this will remove the old model and create a new one - useful for certain parameter changes, but should be avoided if possible. This function is NOT required to use other parts of the module - by default they will create the model if it's not found, or use the one already initialized; this adds control over exactly what model is being used.\n\n\
options [default=None]: when no options object is passed, this removes the old energy model and does not create a new one.\n")
	},
	{ "run_system", (PyCFunction) System_run_system,
	  METH_VARARGS, PyDoc_STR(" \
run_system( options )\n\
Run the system defined by the passed in Options object.\n")
	},
	{ NULL, NULL, 0, NULL } /*Sentinel*/
};

static struct PyModuleDef moduledef = {
	PyModuleDef_HEAD_INIT,
	.m_name = "system",
	.m_doc = "Base module for holding System objects.",
	.m_size = -1,
	.m_methods = System_methods,
};

PyMODINIT_FUNC PyInit_system(void) {
	PyObject *m = Py_None;
	/* Finalize the simulation system object type */
	if (PyType_Ready(&SimSystem_Type) < 0)
		return m;

	m = PyModule_Create(&moduledef);
	if (m == NULL)
		return m;

	Py_INCREF(&SimSystem_Type);
	PyModule_AddObject(m, "SimSystem", (PyObject *) &SimSystem_Type);
    return m;
}
