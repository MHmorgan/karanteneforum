
MAIN=karanteneforum.py

all : run

run :
	python3.8 $(MAIN)

debug :
	python3.8 $(MAIN) DEBUG
