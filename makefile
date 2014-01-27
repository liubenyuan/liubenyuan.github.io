all : jemdoc/*.jemdoc
	python2 jemdoc.py -o tmsbl.html jemdoc/tmsbl.jemdoc
	python2 jemdoc.py -o bsbl.html jemdoc/bsbl.jemdoc
	python2 jemdoc.py -o stsbl.html jemdoc/stsbl.jemdoc
	python2 jemdoc.py -o index.html jemdoc/index.jemdoc
	python2 jemdoc.py -o publications.html jemdoc/publications.jemdoc
	python2 jemdoc.py -o talks.html jemdoc/talks.jemdoc
	python2 jemdoc.py -o resources.html jemdoc/resources.jemdoc
	python2 jemdoc.py -o misc.html jemdoc/misc.jemdoc
	python2 jemdoc.py -o bsbl_fm.html jemdoc/bsbl_fm.jemdoc
	python2 jemdoc.py -o pyhsmm.html jemdoc/pyhsmm.jemdoc
