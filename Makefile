DOCS = index publications
DOCS += bsbl eit connectomics
DOCS += nudtpaper mathjax

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

