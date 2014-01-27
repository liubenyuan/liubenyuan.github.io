all : jemdoc/*.jemdoc
	python2 jemdoc.py -o index.html jemdoc/index.jemdoc
	python2 jemdoc.py -o publications.html jemdoc/publications.jemdoc
	python2 jemdoc.py -o bsbl.html jemdoc/bsbl.jemdoc
	python2 jemdoc.py -o eit.html jemdoc/eit.jemdoc
	python2 jemdoc.py -o radar.html jemdoc/radar.jemdoc
	python2 jemdoc.py -o nrf51822.html jemdoc/nrf51822.jemdoc
	python2 jemdoc.py -o nudtpaper.html jemdoc/nudtpaper.jemdoc
	python2 jemdoc.py -o index.html jemdoc/index.jemdoc
