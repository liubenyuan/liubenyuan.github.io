DOCS = index publications bsbl eit nudtpaper nrf51822 phealth
DOCS += nircm kicad connectomics mathjax udpip

HDOCS=$(addsuffix .html, $(DOCS))
# PHDOCS=$(addprefix html/, $(HDOCS))

.PHONY : all
%.html : jemdoc/%.jemdoc MENU jemdoc.py private.css mysite.conf
	python2 jemdoc.py -c mysite.conf -o $@ $<

.PHONY : docs
docs : $(HDOCS)

.PHONY : clean
clean :
	rm -f *.html

