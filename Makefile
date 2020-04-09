
export FLASK_APP?=karantene_forum.py

all : run

run : debug

debug : export FLASK_ENV=development
debug :
	flask run