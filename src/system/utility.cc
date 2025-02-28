/*
Multistrand nucleic acid kinetic simulator
Copyright (c) 2008-2023 California Institute of Technology. All rights reserved.
The Multistrand Team (help@multistrand.org)
*/

#include "utility.h"
#include <string>
#include <sstream>
#include "move.h"
#include <energymodel.h>
#include "basetype.h"

char* utility::copyToCharArray(string& myString) {

	char* newArray = (char *) new char[myString.length() + 1];
	strcpy(newArray, myString.c_str());

	return newArray;

}

string utility::sequenceToString(BaseType* sequence, int size) {

	// the first and final character is the paired base -- adjust the print for this.

	std::stringstream ss;

	BaseType preBase = (BaseType) sequence[0];
	BaseType postBase = (BaseType) sequence[size + 1];

	if (preBase < 0 || preBase > 5) {
		cout << "Warning! prebase is outside of range" << endl;
	}

	if (postBase < 0 || postBase > 5) {
		cout << "Warning! postbase is outside of range: " << postBase <<endl;
	}

	ss << "";
	ss << baseTypeString[(BaseType) sequence[0]];
	ss << ":";

	for (int i = 1; i < size + 1; i++) {

		ss << baseTypeString[(BaseType) sequence[i]];

	}

	ss << ":";
	ss << baseTypeString[(BaseType) sequence[size + 1]];
	ss << "";

	return ss.str();

}

string utility::copyToString(char* inputCharArray) {

	char* newArray = (char *) new char[strlen(inputCharArray) + 1];
	strcpy(newArray, inputCharArray);

	return string(newArray);

}

string utility::moveType(int type) {

	std::stringstream ss;

	if (type & MOVE_INVALID) {

		ss << "invalid";

	}

	if (type & MOVE_CREATE) {

		ss << "create";

	}

	if (type & MOVE_DELETE) {

		ss << "delete";

	}

	if (type & MOVE_SHIFT) {

		ss << "shift";

	}

	if (type & MOVE_1) {

		ss << "_1, ";

	}

	if (type & MOVE_2) {

		ss << "_2, ";

	}

	if (type & MOVE_3) {

		ss << "_3, ";

	}

	string output = ss.str();

	return output;

}
