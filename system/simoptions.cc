/*
 * simOptions.cc
 *
 *  Created on: Jun 5, 2016
 *      Author: Frits Dannenberg
 */

#include "options.h"	 // python options helper
#include "ssystem.h"
#include "simoptions.h"
#include "energyoptions.h"
#include "scomplex.h"

#include <time.h>
#include <vector>
#include <iostream>
#include <string>
#include <sstream>
#include <cstring>

using std::vector;
using std::string;

SimOptions::SimOptions(void) {

// empty constructor

	simulation_mode = NULL;
	simulation_count = NULL;
	o_interval = NULL;
	o_time = NULL;
	stop_options = NULL;
	stop_count = NULL;
	max_sim_time = NULL;
	seed = NULL;
	myStopComplexes = NULL;
	fixedRandomSeed = false;

	myEnergyOptions = NULL;
	myComplexes = NULL;

}

SimOptions::~SimOptions(void) {

// empty deconstructor

}

PSimOptions::PSimOptions(void) :
		PSimOptions(NULL) {
// Delegated constructor

}

PSimOptions::PSimOptions(PyObject* input) :
		SimOptions() {
	// Inherited constructor.

	python_settings = input;

	// initializers calling python object -- these can use a super object getter.
	// Not clear at the moment if calling all settings is possible without crashing.
	getBoolAttr(python_settings, initial_seed_flag, &fixedRandomSeed);

	if (fixedRandomSeed) {

		getLongAttr(python_settings, initial_seed, &seed);

	}

	myEnergyOptions = new PEnergyOptions(python_settings);

	getLongAttr(python_settings, simulation_mode, &simulation_mode);
	getLongAttr(python_settings, num_simulations, &simulation_count);
	getLongAttr(python_settings, output_interval, &o_interval);
	getDoubleAttr(python_settings, output_time, &o_time);
	getLongAttr(python_settings, stop_count, &stop_count);
	getLongAttr(python_settings, use_stop_conditions, &stop_options);
	getDoubleAttr(python_settings, simulation_time, &max_sim_time);


	debug = false;	// this is the main switch for simOptions debug, for now.

}

string SimOptions::toString() {

	std::stringstream ss;

	ss << "simulation_mode = " << simulation_mode << " \n";
	ss << "simulation_count = " << simulation_count << " \n";
	ss << "o_interval = " << o_interval << " \n";
	ss << "o_time = " << o_time << " \n";
	ss << "stop_options = " << stop_options << " \n";
	ss << "stop_count = " << stop_count << " \n";
	ss << "max_sim_time = " << max_sim_time << " \n";
	ss << "seed = " << seed << " \n";

	ss << "myComplexes = { ";

	for (int i = 0; i < myComplexes->size(); i++) {

		ss << "{ " << myComplexes->at(i).sequence << ", "
				<< myComplexes->at(i).structure << " }";
		// something wrong with tostring of python IDs
		//ss << myComplexes->at(i).list->toString() << " }";

	}

	ss << "} \n";

	ss << " myStopComplexes = { ";

	// linked list iterator
	stopComplexes* myStopComplex = myStopComplexes; // copying pointer so we can iterate.

//	while (myStopComplex != NULL) {
//
////		ss << "{ " << myStopComplex->toString() << " } ";
//		myStopComplex = myStopComplex->next;
//		// something wrong with tostring of python IDs
//		//	ss << "{ " << myStopComplexes->at(i).sequence << ", "
//		//			<< myStopComplexes->at(i).structure  <<  " }";
//
//	}

	ss << "} \n";

	string output = ss.str();

	output += myEnergyOptions->toString();

	return output;

}

bool SimOptions::useFixedRandomSeed() {

	return fixedRandomSeed;

}

long SimOptions::getInitialSeed() {

	return seed;

}

EnergyOptions* SimOptions::getEnergyOptions() {

	return myEnergyOptions;

}

long SimOptions::getSimulationMode(void) {

	return simulation_mode;

}

long SimOptions::getSimulationCount(void) {

	return simulation_count;

}

long SimOptions::getOInterval(void) {

	return o_interval;

}

double SimOptions::getOTime(void) {

	return o_time;

}

long SimOptions::getStopOptions(void) {

	return stop_options;

}

long SimOptions::getStopCount(void) {

	return stop_count;

}

double SimOptions::getMaxSimTime(void) {


	return max_sim_time;

}

//long PSimOptions::getSimulationMode(void) {
//
//	if (simulation_mode == NULL) {
//
//		getLongAttr(python_settings, simulation_mode, &simulation_mode);
//
//		if (debug) {
//
//			printf("The simulation mode is %li \n", simulation_mode);
//
//		}
//
//	}
//
//	return simulation_mode;
//
//}

//long PSimOptions::getSimulationCount(void) {
//
//	if (simulation_count == NULL) {
//
//		getLongAttr(python_settings, num_simulations, &simulation_count);
//
//		if (debug) {
//
//			printf("The simulation count is %li \n", simulation_count);
//
//		}
//
//	}
//
//	return simulation_count;
//
//}

//long PSimOptions::getOInterval(void) {
//
//	if (o_interval == NULL) {
//
//		getLongAttr(python_settings, output_interval, &o_interval);
//
//		if (debug) {
//
//			printf("The o interval is %li \n", o_interval);
//
//		}
//
//	}
//
//	return o_interval;
//
//}

//double PSimOptions::getOTime(void) {
//
//	if (o_time == NULL) {
//
//		getDoubleAttr(python_settings, output_time, &o_time);
//
//		if (debug) {
//
//			printf("The output time is %li \n", o_time);
//
//		}
//
//	}
//
//	return o_time;
//
//}

//void PSimOptions::incrementTrajectoryCount(void) {
//
//	if (python_settings != NULL) {
//		pingAttr(python_settings, increment_trajectory_count);
//	}
//
//}

//long PSimOptions::getStopOptions(void) {
//
//	if (stop_options == NULL) {
//
//		getLongAttr(python_settings, use_stop_conditions, &stop_options);
//
//		if (debug) {
//
//			printf("The stop option is %li \n", stop_options);
//
//		}
//
//	}
//
//	return stop_options;
//
//}
//
//long PSimOptions::getStopCount(void) {
//
//	if (stop_count == NULL) {
//
//		getLongAttr(python_settings, stop_count, &stop_count);
//
//		if (debug) {
//
//			printf("The stop count is %li \n", stop_count);
//
//		}
//
//	}
//
//	return stop_count;
//
//}

//double PSimOptions::getMaxSimTime(void) {
//
//	if (max_sim_time == NULL) {
//
//		getDoubleAttr(python_settings, simulation_time, &max_sim_time);
//
//		if (debug) {
//
//			printf("The max sim time is %d \n", max_sim_time);
//
//		}
//
//	}
//
//	return max_sim_time;
//
//}

//void PSimOptions::sendTransitionInfo(PyObject *transition_tuple) {
//
//	if (python_settings != NULL) {
//
//		pushTransitionInfo(python_settings, transition_tuple);
//
//	}
//
//}

PyObject* PSimOptions::getPythonSettings() {

	return python_settings;

}

void PSimOptions::generateComplexes(PyObject *alternate_start,
		long current_seed) {

	myComplexes = new vector<complex_input>(0); // wipe the pointer to the previous object;

	PyObject *py_start_state = NULL, *py_complex = NULL;
	PyObject *py_seq = NULL, *py_struc = NULL;
	PyObject *py_err = NULL;

	if (myComplexes->size() == 0) {

		complex_input *tempcomplex = NULL;
		char *sequence, *structure;
		class identList *id;
		int start_count;
		PyObject *py_start_state = NULL, *py_complex = NULL;
		PyObject *py_seq = NULL, *py_struc = NULL;
		PyObject *py_err = NULL;

		if (alternate_start != NULL)
			py_start_state = alternate_start;
		else
			py_start_state = getListAttr(python_settings, start_state);

		start_count = PyList_GET_SIZE(py_start_state);
		// doesn't need reference counting for this size call.
		// the getlistattr call we decref later.

		for (int index = 0; index < start_count; index++) {

			// #ifndef DEBUG_MACROS
			py_complex = PyList_GET_ITEM(py_start_state, index);
			// Borrowed reference, we do NOT decref it at end of loop.

#ifdef DEBUG_MACROS
			printPyError_withLineNumber();
#endif

			sequence = getStringAttr(py_complex, sequence, py_seq);
			// new reference

			structure = getStringAttr(py_complex, structure, py_struc);
			// new reference
			// Need to check if an error occurred, specifically, it could be an IOError due to sample failing. If so, we need to get the heck out of dodge right now.
			py_err = PyErr_Occurred();
			// py_err is a borrowed reference

			if (py_err != NULL) { // then an error occurred while getting the structure. Test for IOError (sample failure):
				if (PyErr_ExceptionMatches(PyExc_IOError)) {
					fprintf(stderr,
							"MULTISTRAND: Starting Structure could not be retrieved for index %d in your options object's start_state. This is likely due to Boltzmann sampling failing: please check that the program 'sample' exists and points correctly to the NUPACK sample binary. Or try 'print o.start_state[%d].structure' where 'o' is your options object and refer to that error message (if any).\n",
							index, index);
				} else {
					fprintf(stderr,
							"MULTISTRAND: An unidentified exception occurred while trying to initialize the system.\n");

				}
				return;
			}

			id = getID_list(python_settings, index, alternate_start);

			complex_input myTempComplex = complex_input(sequence, structure,
					id);

			// StrandComplex does make its own copy of the seq/structure, so we can now decref.
			myComplexes->push_back(myTempComplex);

			Py_DECREF(py_seq);
			Py_DECREF(py_struc);

		}
		Py_DECREF(py_start_state);

		// Update the current seed and store the starting structures
		//   note: only if we actually have a system_options, e.g. no alternate start
		if (alternate_start == NULL && python_settings != NULL) {
			setLongAttr(python_settings, interface_current_seed, current_seed);
		}
		seed = current_seed;

	}

	return;
}

stopComplexes* PSimOptions::getStopComplexes(int) {

	myStopComplexes = getStopComplexList(python_settings, 0);

	return myStopComplexes;

}

void PSimOptions::stopResultError(long seed) {

	printStatusLine(python_settings, seed, STOPRESULT_ERROR, 0.0, NULL);
	return;

}

void PSimOptions::stopResultNan(long seed) {

	printStatusLine(python_settings, seed, STOPRESULT_NAN, 0.0, NULL);
	return;

}

void PSimOptions::stopResultNormal(long seed, double time, char* message) {

	printStatusLine(python_settings, seed, STOPRESULT_NORMAL, time, message);
	return;

}

void PSimOptions::stopResultTime(long seed, double time) {

	printStatusLine(python_settings, seed, STOPRESULT_TIME, time, NULL);
	return;

}

void PSimOptions::stopResultBimolecular(string type, long seed, double stopTime,
		double rate, char* message) {

	if (type.compare("Reverse")) {

		printStatusLine_First_Bimolecular(python_settings, seed,
				STOPRESULT_REVERSE, stopTime, rate, message);

	} else if (type.compare("Forward")) {

		printStatusLine_First_Bimolecular(python_settings, seed,
				STOPRESULT_FORWARD, stopTime, rate, message);

	} else if (type.compare("FTime")) {

		printStatusLine_First_Bimolecular(python_settings, seed,
				STOPRESULT_FTIME, stopTime, rate, NULL);

	} else if (type.compare("NoMoves")) {
		printStatusLine_First_Bimolecular(python_settings, seed,
				STOPRESULT_NOMOVES, stopTime, rate, NULL);

	}

}

