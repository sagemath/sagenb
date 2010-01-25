# -*- makefile -*-
# Makefile for the Sage Notebook project (http://nb.sagemath.org/).
# GNU make help: http://www.gnu.org/software/make/manual

SAGE = sage
HG = $(SAGE) -hg
PYTHON = $(SAGE) -python
SETUP = $(PYTHON) setup.py

install:
	$(SETUP) install

develop:
	$(SETUP) develop

update:
	$(HG) pull http://boxen.math.washington.edu:8100
	$(HG) update

doc:	doc-jsmath
doc-pngmath:
	$(SAGE) -docbuild reference html $(OPTS)
doc-jsmath:
	$(SAGE) -docbuild reference html -j $(OPTS)

test:
	$(SAGE) -t -sagenb $(OPTS)
ptest:
	$(SAGE) -tp \
	`$(PYTHON) -c "import multiprocessing as m; print m.cpu_count()"` \
	-sagenb $(OPTS)

spkg:
	./spkg-dist

.PHONY:	clean distclean
