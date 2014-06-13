DOCS = index publications bsbl eit radar nudtpaper nrf51822 phealth nircm kicad msp430 connectomics flexbot atmel

HDOCS=$(addsuffix .html, $(DOCS))
# PHDOCS=$(addprefix html/, $(HDOCS))

.PHONY : all
%.html : jemdoc/%.jemdoc MENU jemdoc.py
	python2 jemdoc.py -o $@ $<

.PHONY : docs
docs : $(HDOCS)

.PHONY : clean
clean :
	rm -f *.html

