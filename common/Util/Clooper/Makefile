CC=gcc


ARCH_OUT = $(shell arch)

CSOUND_ARCH = $(shell if [ -z "$(shell arch | grep arm)" ]; then \
        echo $(ARCH_OUT) | grep 64 >/dev/null && echo linux64 || echo linux32; \
    else \
        echo $(ARCH_OUT); \
    fi)

CSOUND_VERSION = $(shell csound --version 2>&1 | grep -o "Csound version [0-9]\+\.[0-9]\+" | awk '{print $$3}' | sed s/\\.//g)
LIB_NAME = $(CSOUND_ARCH)_$(CSOUND_VERSION)

CXXFLAGS = $(shell python-config --cflags) \
		   -Wall -Werror -fPIC -O2 -finline 
LDFLAGS+=  $(python-config --libs) \
		   -lcsound

all : aclient.so
	rm -rf $(LIB_NAME)
	mkdir $(LIB_NAME)
	strip aclient.so
	mv aclient.so $(LIB_NAME)/
	touch $(LIB_NAME)/__init__.py

aclient.so : aclient.cpp
	g++ $(CXXFLAGS) -shared -o $@ $< $(LDFLAGS)

clean :
	rm aclient*.so

