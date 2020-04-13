
export FLASK_APP?=karantene_forum.py

all : run

run :
	python3.8 -m flask run -h 0.0.0.0 -p 4202 &> karanteneforum.log

debug : export FLASK_ENV=development
debug :
	flask run
