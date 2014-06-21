DOCS = index publications bsbl eit radar nudtpaper nrf51822 phealth nircm kicad msp430 connectomics flexbot atmel mathjax

HDOCS=$(addsuffix .html, $(DOCS))
# PHDOCS=$(addprefix html/, $(HDOCS))

.PHONY : all
%.html : jemdoc/%.jemdoc MENU jemdoc.py
	python2 jemdoc.py -c mysite.conf -o $@ $<

.PHONY : docs
docs : $(HDOCS)

.PHONY : clean
clean :
	rm -f *.html

