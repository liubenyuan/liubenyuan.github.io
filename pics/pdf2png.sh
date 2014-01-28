#!/bin/bash
## no space in '=', there will be errors if so.

if [ $# -ne 1 ]; then echo "EE: 1 arguments (convert .pdf file) expected, exit"; exit 1; fi

_convname="$1"
_filename=$(basename $1 .pdf) # "${_convname##*/}"
pdfcrop ${_convname}
convert -colorspace RGB -interlace none -density 300x300 -quality 100 "${_filename}-crop.pdf" "${_filename}.png"
rm -v "${_filename}-crop.pdf"

