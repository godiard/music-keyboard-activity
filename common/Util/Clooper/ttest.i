
%module ttest

%{
#define SWIG_FILE_WITH_INIT
#include "ttest.h"
%}

%pythoncode
%{
def somefn(seed, mat):

%}

%include "ttest.h"
