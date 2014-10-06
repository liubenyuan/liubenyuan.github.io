#!/usr/bin/env python

"""jemdoc version 0.7.3, 2012-11-27."""

# Copyright (C) 2007-2012 Jacob Mattingley (jacobm@stanford.edu).
#
# This file is part of jemdoc.
#
# jemdoc is free software; you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation; either version 3 of the License, or (at your option) any later
# version.
#
# jemdoc is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
#
# The LaTeX equation portions of this file were initially based on
# latexmath2png, by Kamil Kisiel (kamil@kamikisiel.net).
#

import sys
import os
import re
import time
import StringIO
from subprocess import *
import tempfile

def info():
  print __doc__
  print 'Platform: ' + sys.platform + '.'
  print 'Python: %s, located at %s.' % (sys.version[:5], sys.executable)
  print 'Equation support:',
  (supported, message) = testeqsupport()
  if supported:
    print 'yes.'
  else:
    print 'no.'
  print message

def testeqsupport():
  supported = True
  msg = ''
  p = Popen('latex --version', shell=True, stdout=PIPE, stderr=PIPE)
  rc = p.wait()
  if rc != 0:
    msg += '  latex: not found.\n'
    supported = False
  else:
    msg += '  latex: ' + p.stdout.readlines()[0].rstrip() + '.\n'
  p = Popen('dvipng --version', shell=True, stdout=PIPE, stderr=PIPE)
  rc = p.wait()
  if rc != 0:
    msg += '  dvipng: not found.\n'
    supported = False
  else:
    msg += '  dvipng: ' + p.stdout.readlines()[0].rstrip() + '.\n'

  return (supported, msg[:-1])

class controlstruct(object):
  def __init__(self, infile, outfile=None, conf=None, inname=None, eqs=True,
         eqdir='eqs', eqdpi=130):
    self.inname = inname
    self.inf = infile
    self.outf = outfile
    self.conf = conf
    self.linenum = 0
    self.otherfiles = []
    self.eqs = eqs
    self.eqdir = eqdir
    self.eqdpi = eqdpi
    # Default to supporting equations until we know otherwise.
    self.eqsupport = True
    self.eqcache = True
    self.eqpackages = []
    self.texlines = []
    self.analytics = None
    self.eqbd = {} # equation base depth.
    self.baseline = None

  def pushfile(self, newfile):
    self.otherfiles.insert(0, self.inf)
    self.inf = open(newfile, 'rb')

  def nextfile(self):
    self.inf.close()
    self.inf = self.otherfiles.pop(0)

def showhelp():
  a = """Usage: jemdoc [OPTIONS] [SOURCEFILE] 
  Produces html markup from a jemdoc SOURCEFILE.

  Most of the time you can use jemdoc without any additional flags.
  For example, typing

    jemdoc index

  will produce an index.html from index.jemdoc, using a default
  configuration.

  Some configuration options can be overridden by specifying a
  configuration file.  You can use

    jemdoc --show-config

  to print a sample configuration file (which includes all of the
  default options). Any or all of the configuration [blocks] can be
  overwritten by including them in a configuration file, and running,
  for example,

    jemdoc -c mywebsite.conf index.jemdoc 

  You can view version and installation details with

    jemdoc --version

  See http://jemdoc.jaboc.net/ for many more details."""
  b = ''
  for l in a.splitlines(True):
    if l.startswith(' '*4):
      b += l[4:]
    else:
      b += l

  print b

def standardconf():
  a = """[firstbit]
  <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN"
    "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
  <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
  <head>
  <meta name="generator" content="jemdoc, see http://jemdoc.jaboc.net/" />
  <meta http-equiv="Content-Type" content="text/html;charset=utf-8" />

  [defaultcss]
  <link rel="stylesheet" href="jemdoc.css" type="text/css" />

  [windowtitle]
  # used in header for window title.
  <title>|</title>

  [fwtitlestart]
  <div id="fwtitle">

  [fwtitleend]
  </div>

  [doctitle]
  # used at top of document.
  <div id="toptitle">
  <h1>|</h1>

  [subtitle]
  <div id="subtitle">|</div>

  [doctitleend]
  </div>

  [bodystart]
  </head>
  <body>

  [analytics]
  <script type="text/javascript">
  var gaJsHost = (("https:" == document.location.protocol) ? "https://ssl." : "http://www.");
  document.write(unescape("%3Cscript src='" + gaJsHost + "google-analytics.com/ga.js' type='text/javascript'%3E%3C/script%3E"));
  </script>
  <script type="text/javascript">
  try {
      var pageTracker = _gat._getTracker("|");
      pageTracker._trackPageview();
  } catch(err) {}</script>

  [specificcss]
  <link rel="stylesheet" href="|" type="text/css" />

  [specificjs]
  <script src="|.js" type="text/javascript"></script>

  [menustart]
  <header class="bg-light">
  <div class="navigation-bar light">
  <div class="navigation-bar-content container">
  <nav class="horizontal-menu"><ul class="element-menu">

  [menuend]
  </ul></nav></div></div>
  </header>
  <div class="page"><div class="page-content margin20"><div class="page-container">

  [menucategory]
  <li><a class="dropdown-toggle" href="#">|</a>
  <ul class="dropdown-menu" data-role="dropdown">

  [menucategoryend]
  </ul></li>

  [menuitem]
  <li><a href="|1"|3>|2</a></li>

  [currentmenuitem]
  <li><a href="|1" class="current"|3>|2</a></li>

  [menulastbit]
  </div></div></div>

  [nomenu]
  <div class="container">

  [nomenulastbit]
  </div>

  [bodyend]
  </body>
  </html>

  [infoblockstart]
  <div class="example margin0"><pre>

  [infoblockend]
  </pre></div>

  [footerstart]
  <div class="panel ribbed-amber"><div class="panel-content">

  [footerend]
  </div></div>

  [lastupdated]
  Page generated |, by <a href="https://github.com/wsshin/jemdoc_mathjax" target="blank">jemdoc+MathJax</a>.

  [sourcelink]
  (<a href="|">source</a>)

  """
  b = ''
  for l in a.splitlines(True):
    if l.startswith('  '):
      b += l[2:]
    else:
      b += l

  return b

class JandalError(Exception):
  pass

class NoEqSupport(Exception):
  pass

def raisejandal(msg, line=0):
  if line == 0:
    s = "%s" % msg
  else:
    s = "line %d: %s" % (line, msg)
  raise JandalError(s)

def readnoncomment(f):
  l = f.readline()
  if l == '':
    return l
  elif l[0] == '#': # jem: be a little more generous with the comments we accept?
    return readnoncomment(f)
  else:
    return l.rstrip() + '\n' # leave just one \n and no spaces etc.

def parseconf(cns):
  syntax = {}
  warn = False # jem. make configurable?
  # manually add the defaults as a file handle.
  fs = [StringIO.StringIO(standardconf())]
  for sname in cns:
    fs.append(open(sname, 'rb'))

  for f in fs:
    while pc(controlstruct(f)) != '':
      l = readnoncomment(f)
      r = re.match(r'\[(.*)\]\n', l)

      if r:
        tag = r.group(1)

        s = ''
        l = readnoncomment(f)
        while l not in ('\n', ''):
          s += l
          l = readnoncomment(f)

        syntax[tag] = s

    f.close()

  return syntax

def insertmenuitems(f, mname, current, prefix):
  m = open(mname, 'rb')

  unclosed_menu_category = 0
  while pc(controlstruct(m)) != '':
    l = readnoncomment(m)
    l = l.strip()
    if l == '':
      continue

    r = re.match(r'\s*(.*?)\s*\[(.*)\]', l)

    if r: # then we have a menu item.
      link = r.group(2)
      if link[0] == '\\':
        option = ' target="blank"'
        link = link[1:]
      else:
        option = ''

      # Don't use prefix if we have an absolute link.
      if '://' not in r.group(2):
        link = prefix + allreplace(link)

      # replace spaces with nbsps.
      # do do this, even though css would make it work - ie ignores.
      # only replace spaces that aren't in {{ blocks.
      in_quote = False
      menuitem = ""
      for group in re.split(r'({{|}})', r.group(1)):
        if in_quote:
          if group == '}}':
            in_quote = False
            next
          else:
            menuitem += group
        else:
          if group == '{{':
            in_quote = True
            next
          else:
            menuitem += br(re.sub(r'(?<!\\n) +', '~', group), f)

      if link[-len(current):] == current:
        hb(f.outf, f.conf['currentmenuitem'], link, menuitem, option)
      else:
        hb(f.outf, f.conf['menuitem'], link, menuitem, option)

    else: # menu category.
      if unclosed_menu_category==1:
        hb(f.outf, f.conf['menucategoryend'], br(l, f))
      unclosed_menu_category = 1
      hb(f.outf, f.conf['menucategory'], br(l, f))

  if unclosed_menu_category==1:
    hb(f.outf, f.conf['menucategoryend'], br(l, f))

  m.close()

def out(f, s):
  f.write(s)

def myussub(link):
  link = link.replace('_', 'UNDERSCORE65358')

  return link

def myusresub(r):
  r = re.sub('UNDERSCORE65358', '_', r)

  return r

def myeqsub(eqtext):
  eqtext = eqtext.replace('\\', 'BACKSLASH65358')
  eqtext = eqtext.replace('[', 'OPENBRACKET65358')
  eqtext = eqtext.replace(']', 'CLOSEBRACKET65358')
  eqtext = eqtext.replace('+', 'PLUS65358')
  eqtext = eqtext.replace('&', 'AMPERSAND65358')
  eqtext = eqtext.replace('<', 'LESSTHAN65358')
  eqtext = eqtext.replace('>', 'GREATERTHAN65358')
#  eqtext = eqtext.replace('\n', ' ')
  eqtext = eqtext.replace('_', 'UNDERSCORE65358')

  return eqtext

def myeqresub(r):
  r = re.sub('BACKSLASH65358', r'\\', r)
  r = re.sub('OPENBRACKET65358', '[', r)
  r = re.sub('CLOSEBRACKET65358', ']', r)
  r = re.sub('PLUS65358', '+', r)
  r = re.sub('AMPERSAND65358', '&', r)
  r = re.sub('LESSTHAN65358', '<', r)
  r = re.sub('GREATERTHAN65358', '>', r)
  r = re.sub('QUOTATION65358', '"', r)
  r = re.sub('UNDERSCORE65358', '_', r)

  return r

def hb(f, tag, content1, content2=None, content3=None):
  """Writes out a halfblock (hb)."""

  if content1 is None:
    content1 = ""

  if content3 is None:
    content3 = ""

  if content2 is None:
#    out(f, re.sub(r'\|', content1, tag))
    r = re.sub(r'\|', content1, tag)
    r = re.sub(r'\|3', content3, r)
    r = myeqresub(r)
    out(f, r)
  else:
    r = re.sub(r'\|1', content1, tag)
    r = re.sub(r'\|3', content3, r)
    r = re.sub(r'\|2', content2, r)
    r = myeqresub(r)
    out(f, r)

def pc(f, ditchcomments=True):
  """Peeks at next character in the file."""
  # Should only be used to look at the first character of a new line.
  c = f.inf.read(1)
  if c: # only undo forward movement if we're not at the end.
    if ditchcomments and c == '#':
      l = nl(f)
      if doincludes(f, l):
        return "#"

    if c in ' \t':
      return pc(f)

    if c == '\\':
      c += pc(f)

    f.inf.seek(-1, 1)
  elif f.otherfiles:
    f.nextfile()
    return pc(f, ditchcomments)

  return c

def doincludes(f, l):
  ir = 'includeraw{'
  i = 'include{'
  if l.startswith(ir):
    nf = open(l[len(ir):-2], 'rb')
    f.outf.write(nf.read())
    nf.close()
  elif l.startswith(i):
    f.pushfile(l[len(i):-2])
  else:
    return False

  return True

def nl(f, withcount=False, codemode=False):
  """Get input file line."""
  s = f.inf.readline()
  if not s and f.otherfiles:
    f.nextfile()
    return nl(f, withcount, codemode)

  f.linenum += 1

  if not codemode:
    # remove any special characters - assume they were checked by pc()
    # before we got here.
    # remove any trailing comments.
    s = s.lstrip(' \t')
    s = re.sub(r'\s*(?<!\\)#.*', '', s)

  if withcount:
    if s[0] == '.':
      m = r'\.'
    else:
      m = s[0]

    r = re.match('(%s+) ' % m, s)
    if not r:
      raise SyntaxError("couldn't handle the jandal (code 12039) on line"
                " %d" % f.linenum)

    if not codemode:
      s = s.lstrip('-.=:')

    return (s, len(r.group(1)))
  else:
    if not codemode:
      s = s.lstrip('-.=:')

    return s

def np(f, withcount=False, eatblanks=True):
  """Gets the next paragraph from the input file."""
  # New paragraph markers signalled by characters in following tuple.
  if withcount:
    (s, c) = nl(f, withcount)
  else:
    s = nl(f)

  while pc(f) not in ('\n', '-', '.', ':', '', '=', '~', '{', '\\(', '\\)'):
    s += nl(f)

  while eatblanks and pc(f) == '\n':
    nl(f) # burn blank line.

  # in both cases, ditch the trailing \n.
  if withcount:
    return (s[:-1], c)
  else:
    return s[:-1]

def quote(s):
  return re.sub(r"""[\\*/+"'<>&$%\.~[\]-]""", r'\\\g<0>', s)

def replacequoted(b):
  """Quotes {{raw html}} sections."""

  r = re.compile(r'\{\{(.*?)\}\}', re.M + re.S)
  m = r.search(b)
  while m:
    qb = quote(m.group(1))

    b = b[:m.start()] + qb + b[m.end():]

    m = r.search(b, m.start())

  return b

def replacepercents(b):
  # replace %sections% as +{{sections}}+. Do not replace if within a link.

  r = re.compile(r'(?<!\\)%(.*?)(?<!\\)%', re.M + re.S)
  m = r.search(b)
  while m:
    #qb = '+' + quote(m.group(1)) + '+'
    a = re.sub(r'\[', r'BSNOTLINKLEFT12039XX', m.group(1))
    a = re.sub(r'\]', r'BSNOTLINKRIGHT12039XX', a)
    qb = '+{{' + a + '}}+'

    b = b[:m.start()] + qb + b[m.end():]

    m = r.search(b, m.start())

  return b

def replaceequations(b, f):
  # replace $sections$ and \(sections\) as equations.
  rs = ((re.compile(r'(?<!\\)\$(.*?)(?<!\\)\$', re.M + re.S), False),
     (re.compile(r'(?<!\\)\\\((.*?)(?<!\\)\\\)', re.M + re.S), True))
  for (r, wl) in rs:
    m = r.search(b)
    while m:
      eq = m.group(1)
      if wl:
        fn = str(abs(hash(eq + 'wl120930alsdk')))
      else:
        fn = str(abs(hash(eq)))

      eqtext = allreplace(eq)
#      print eqtext
#      eqtext = eqtext.replace('\\', '')
      eqtext = myeqsub(eqtext)

      # Double braces will cause problems with escaping of image tag.
      eqtext = eqtext.replace('{{', 'DOUBLEOPENBRACE')
      eqtext = eqtext.replace('}}', 'DOUBLECLOSEBRACE')

      if wl:
#        b = b[:m.start()] + \
#            '{{\n<div class="eqwl"><img class="eqwl" src="%s" alt="%s" />\n<br /></div>}}' % (fullfn, eqtext) + b[m.end():]
        #b = b[:m.start()] + 'BACKSLASH65358OPENBRACKET65358\n' + eqtext + '\nBACKSLASH65358CLOSEBRACKET65358'+ b[m.end():]
        b = b[:m.start()] + 'BACKSLASH65358OPENBRACKET65358' + eqtext + 'BACKSLASH65358CLOSEBRACKET65358'+ b[m.end():]
        #b = b[:m.start()] + 'BACKSLASH(BACKSLASHbegin{equation}\n' + eqtext + '\nBACKSLASHend{equation}BACKSLASH)'+ b[m.end():]
        b = '<p style=QUOTATION65358text-align:centerQUOTATION65358>\n' + b + '\n</p>'
        b = myeqsub(b)
      else:
#        b = b[:m.start()] + \
#          '{{<img class="eq" src="%s" alt="%s" style="vertical-align: -%dpx" />}}' % (fullfn, eqtext, offset) + b[m.end():]
        b = b[:m.start()] + 'BACKSLASH65358(' + eqtext + 'BACKSLASH65358)' + b[m.end():]

      # jem: also clean out line breaks in the alttext?
      m = r.search(b, m.start())

  return replacequoted(b)

def replaceimages(b):
  # works with [img{width}{height}{alttext} location caption].
  r = re.compile(r'(?<!\\)\[img((?:\{.*?\}){,3})\s(.*?)(?:\s(.*?))?(?<!\\)\]',
           re.M + re.S)
  m = r.search(b)
  s = re.compile(r'{(.*?)}', re.M + re.S)
  while m:
    m1 = list(s.findall(m.group(1)))
    m1 += ['']*(3 - len(m1))

    bits = []
    link = m.group(2).strip()
    bits.append(r'src=\"%s\"' % quote(link))

    if m1[0]:
      if m1[0].isdigit():
        s = m1[0] + 'px'
      else:
        s = m1[0]
      bits.append(r'width=\"%s\"' % quote(s))
    if m1[1]:
      if m1[1].isdigit():
        s = m1[1] + 'px'
      else:
        s = m1[1]
      bits.append(r'height=\"%s\"' % quote(s))
    if m1[2]:
      bits.append(r'alt=\"%s\"' % quote(m1[2]))
    else:
      bits.append(r'alt=\"\"')

    b = b[:m.start()] + r'<img %s />' % " ".join(bits) + b[m.end():]

    m = r.search(b, m.start())

  return b

def replacelinks(b):
  # works with [link.html new link style].
  r = re.compile(r'(?<!\\)\[(.*?)(?:\s(.*?))?(?<!\\)\]', re.M + re.S)
  m = r.search(b)
  while m:
    m1 = m.group(1).strip()

    if m1[0] == '/':
        option = ''
        m1 = m1[1:]
    else:
        option = ' target="blank"'

    if '@' in m1 and not m1.startswith('mailto:') and not \
       m1.startswith('http://'):
      link = 'mailto:' + m1
    else:
      link = m1

    # first unquote any hashes (e.g. for in-page links).
    link = re.sub(r'\\#', '#', link)

    # remove any +{{ or }}+ links.
    link = re.sub(r'(\+\{\{|\}\}\+)', r'%', link)

    link = quote(link)
    link = myussub(link)  # to prevent _ in address from changing

    if m.group(2):
      linkname = m.group(2).strip()
    else:
      # remove any mailto before labelling.
      linkname = re.sub('^mailto:', '', link)

    b = b[:m.start()] + r'<a href=\"%s\"%s>%s<\/a>' % (link, option, linkname) + b[m.end():]

    m = r.search(b, m.start())

  return b

def br(b, f, tableblock=False):
  """Does simple text replacements on a block of text. ('block replacements')"""

  # Deal with environment variables (say, for Michael Grant).
  r = re.compile(r"!\$(\w{2,})\$!", re.M + re.S)

  for m in r.findall(b):
    repl = os.environ.get(m)
    if repl == None:
      b = re.sub("!\$%s\$!" % m, 'FAILED_MATCH_' + m, b)
    else:
      b = re.sub("!\$%s\$!" % m, repl, b)

  # Deal with literal backspaces.
  if f.eqs and f.eqsupport:
    b = replaceequations(b, f)

  b = re.sub(r'\\\\', 'jemLITerl33talBS', b)

  # Deal with {{html embedding}}.
  b = replacequoted(b)

  b = allreplace(b)

  b = b.lstrip('-. \t') # remove leading spaces, tabs, dashes, dots.
  b = replaceimages(b) # jem not sure if this is still used.

  # Slightly nasty hackery in this next bit.
  b = replacepercents(b)
  b = replacelinks(b)
  b = re.sub(r'BSNOTLINKLEFT12039XX', r'[', b)
  b = re.sub(r'BSNOTLINKRIGHT12039XX', r']', b)
  b = replacequoted(b)

  # Deal with /italics/ first because the '/' in other tags would otherwise
  # interfere.
  r = re.compile(r'(?<!\\)/(.*?)(?<!\\)/', re.M + re.S)
  b = re.sub(r, r'<em>\1</em>', b)

  # Deal with *bold*. (metro)
  r = re.compile(r'(?<!\\)\*(.*?)(?<!\\)\*', re.M + re.S)
  b = re.sub(r, r'<strong>\1</strong>', b)

  # Deal with _underscore_. (metro)
  r = re.compile(r'(?<!\\)_(.*?)(?<!\\)_', re.M + re.S)
  b = re.sub(r, r'<u><strong>\1</strong></u>', b)
  b = myusresub(b)

  # Deal with +monospace+.
  r = re.compile(r'(?<!\\)\+(.*?)(?<!\\)\+', re.M + re.S)
  b = re.sub(r, r'<code>\1</code>', b)

  # Deal with "double quotes".
  r = re.compile(r'(?<!\\)"(.*?)(?<!\\)"', re.M + re.S)
  b = re.sub(r, r'&ldquo;\1&rdquo;', b)

  # Deal with left quote `.
  r = re.compile(r"(?<!\\)`", re.M + re.S)
  b = re.sub(r, r'&lsquo;', b)

  # Deal with apostrophe '.
  # Add an assertion that the next character's not a letter, to deal with
  # apostrophes properly.
  r = re.compile(r"(?<!\\)'(?![a-zA-Z])", re.M + re.S)
  b = re.sub(r, r'&rsquo;', b)

  # Deal with em dash ---.
  r = re.compile(r"(?<!\\)---", re.M + re.S)
  b = re.sub(r, r'&#8201;&mdash;&#8201;', b)

  # Deal with en dash --.
  r = re.compile(r"(?<!\\)--", re.M + re.S)
  b = re.sub(r, r'&ndash;', b)

  # Deal with ellipsis ....
  r = re.compile(r"(?<!\\)\.\.\.", re.M + re.S)
  b = re.sub(r, r'&hellip;', b)

  # Deal with non-breaking space ~.
  r = re.compile(r"(?<!\\)~", re.M + re.S)
  b = re.sub(r, r'&nbsp;', b)
  b = re.sub('TILDE', '~', b)

  # Deal with registered trademark \R.
  r = re.compile(r"(?<!\\)\\R", re.M + re.S)
  b = re.sub(r, r'&reg;', b)

  # Deal with copyright \C.
  r = re.compile(r"(?<!\\)\\C", re.M + re.S)
  b = re.sub(r, r'&copy;', b)

  # Deal with middot \M.
  r = re.compile(r"(?<!\\)\\M", re.M + re.S)
  b = re.sub(r, r'&middot;', b)

  # Deal with line break.
  r = re.compile(r"(?<!\\)\\n", re.M + re.S)
  b = re.sub(r, r'<br />', b)

  # Deal with paragraph break. Caution! Should only use when we're already in
  # a paragraph.
  r = re.compile(r"(?<!\\)\\p", re.M + re.S)
  b = re.sub(r, r'</p><p class="readable-text">', b)

  if tableblock:
    # Deal with ||, meaning </td></tr><tr><td>
    r = re.compile(r"(?<!\\)\|\|", re.M + re.S)
    f.tablecol = 2
    bcopy = b
    b = ""
    r2 = re.compile(r"(?<!\\)\|", re.M + re.S)
    for l in bcopy.splitlines():
      f.tablerow += 1
      l = re.sub(r, r'</td></tr>\n<tr class="r%d"><td class="c1">' \
            % f.tablerow, l)

      l2 = ''
      col = 2
      r2s = r2.split(l)
      for x in r2s[:-1]:
        l2 += x + ('</td><td class="c%d">' % col) # text-center, text-right
        col += 1
      l2 += r2s[-1]

      b += l2

  # Second to last, remove any remaining quoting backslashes.
  b = re.sub(r'\\(?!\\)', '', b)

  # Deal with literal backspaces.
  b = re.sub('jemLITerl33talBS', r'\\', b)

  # Also fix up DOUBLEOPEN and DOUBLECLOSEBRACES.
  b = re.sub('DOUBLEOPENBRACE', '{{', b)
  b = re.sub('DOUBLECLOSEBRACE', '}}', b)

  return b

def allreplace(b):
  """Replacements that should be done on everything."""
  r = re.compile(r"(?<!\\)&", re.M + re.S)
  b = re.sub(r, r'&amp;', b)

  r = re.compile(r"(?<!\\)>", re.M + re.S)
  b = re.sub(r, r'&gt;', b)

  r = re.compile(r"(?<!\\)<", re.M + re.S)
  b = re.sub(r, r'&lt;', b)

  return b

def pyint(f, l):
  l = l.rstrip()
  l = allreplace(l)

  r = re.compile(r'(#.*)')
  l = r.sub(r'<span class = "comment">\1</span>', l)

  if l.startswith('&gt;&gt;&gt;'):
    hb(f, '<span class="pycommand">|</span>\n', l)
  else:
    out(f, l + '\n')

def putbsbs(l):
  for i in range(len(l)):
    l[i] = '\\b' + l[i] + '\\b'

  return l

def geneq(f, eq, dpi, wl, outname):
  # First check if there is an existing file.
  eqname = os.path.join(f.eqdir, outname + '.png')

  eqdepths = {}
  if f.eqcache:
    try:
      dc = open(os.path.join(f.eqdir, '.eqdepthcache'), 'rb')
      for l in dc:
        a = l.split()
        eqdepths[a[0]] = int(a[1])
      dc.close()

      if os.path.exists(eqname) and eqname in eqdepths:
        return (eqdepths[eqname], eqname)
    except IOError:
      print 'eqdepthcache read failed.'

  # Open tex file.
  tempdir = tempfile.gettempdir()
  fd, texfile = tempfile.mkstemp('.tex', '', tempdir, True)
  basefile = texfile[:-4]
  g = os.fdopen(fd, 'wb')

  preamble = '\documentclass{article}\n'
  for p in f.eqpackages:
    preamble += '\usepackage{%s}\n' % p
  for p in f.texlines:
    # Replace \{ and \} in p with { and }.
    # XXX hack.
    preamble += re.sub(r'\\(?=[{}])', '', p + '\n')
  preamble += '\pagestyle{empty}\n\\begin{document}\n'
  g.write(preamble)
  
  # Write the equation itself.
  if wl:
    g.write('\\[%s\\]' % eq)
  else:
    g.write('$%s$' % eq)

  # Finish off the tex file.
  g.write('\n\\newpage\n\end{document}')
  g.close()

  exts = ['.tex', '.aux', '.dvi', '.log']
  try:
    # Generate the DVI file
    latexcmd = 'latex -file-line-error-style -interaction=nonstopmode ' + \
         '-output-directory %s %s' % (tempdir, texfile)
    p = Popen(latexcmd, shell=True, stdout=PIPE)
    rc = p.wait()
    if rc != 0:
      for l in p.stdout.readlines():
        print '  ' + l.rstrip()
      exts.remove('.tex')
      raise Exception('latex error')

    dvifile = basefile + '.dvi'
    dvicmd = 'dvipng --freetype0 -Q 9 -z 3 --depth -q -T tight -D %i -bg Transparent -o %s %s' % (dpi, eqname, dvifile)
    # discard warnings, as well.
    p = Popen(dvicmd, shell=True, stdout=PIPE, stderr=PIPE)
    rc = p.wait()
    if rc != 0:
      print p.stderr.readlines()
      raise Exception('dvipng error')
    depth = int(p.stdout.readlines()[-1].split('=')[-1])
  finally:
    # Clean up.
    for ext in exts:
      g = basefile + ext
      if os.path.exists(g):
        os.remove(g)

  # Update the cache if we're using it.
  if f.eqcache and eqname not in eqdepths:
    try:
      dc = open(os.path.join(f.eqdir, '.eqdepthcache'), 'ab')
      dc.write(eqname + ' ' + str(depth) + '\n')
      dc.close()
    except IOError:
      print 'eqdepthcache update failed.'
  return (depth, eqname)

def dashlist(f, ordered=False):
  level = 0

  if ordered:
    char = '.'
    ul = 'ol'
  else:
    char = '-'
    ul = 'ul'

  while pc(f) == char:
    (s, newlevel) = np(f, True, False)

    # first adjust list number as appropriate.
    if newlevel > level:
      for i in range(newlevel - level):
        if newlevel > 1:
          out(f.outf, '\n')
        out(f.outf, '<%s>\n<li>' % ul)
    elif newlevel < level:
      out(f.outf, '\n</li>')
      for i in range(level - newlevel):
        #out(f.outf, '</li>\n</%s>\n</li><li>' % ul)
        # demote means place '</ul></li>' in the file.
        out(f.outf, '</%s>\n</li>' % ul)
      #out(f.outf, '\n<li>')
      out(f.outf, '\n<li>')
    else:
      # same level, make a new list item.
      out(f.outf, '\n</li>\n<li>')

    out(f.outf, '<p class="readable-text">' + myeqresub(br(s, f)) + '</p>')
    level = newlevel

  for i in range(level):
    out(f.outf, '\n</li>\n</%s>\n' % ul)

def colonlist(f):
  out(f.outf, '<dl>\n')
  while pc(f) == ':':
    s = np(f, eatblanks=False)
    r = re.compile(r'\s*{(.*?)(?<!\\)}(.*)', re.M + re.S)
    g = re.match(r, s)

    if not g or len(g.groups()) != 2:
      raise SyntaxError("couldn't handle the jandal (invalid deflist "
               "format) on line %d" % f.linenum)
    # split into definition / non-definition part.
    defpart = g.group(1)
    rest = g.group(2)

    hb(f.outf, '<dt>|</dt>\n', br(defpart, f))
    hb(f.outf, '<dd><p class="readable-text">|</p></dd>\n', br(rest, f))

  out(f.outf, '</dl>\n')

def prependnbsps(l):
  g = re.search('(^ *)(.*)', l).groups()
  return g[0].replace(' ', '&nbsp;') + g[1]

def inserttitle(f, t):
  if t is not None:
    hb(f.outf, f.conf['doctitle'], t)

    # Look for a subtitle.
    if pc(f) != '\n':
      hb(f.outf, f.conf['subtitle'], br(np(f), f))

    hb(f.outf, f.conf['doctitleend'], t)

def procfile(f):
  f.linenum = 0

  menu = None
  # convert these to a dictionary.
  showfooter = True
  showsourcelink = False
  showlastupdated = True
  showlastupdatedtime = True
  nodefaultcss = False
  fwtitle = False
  css = []
  js = []
  title = None
  while pc(f, False) == '#':
    l = f.inf.readline()
    f.linenum += 1
    if doincludes(f, l[1:]):
      continue
    if l.startswith('# jemdoc:'):
      l = l[len('# jemdoc:'):]
      a = l.split(',')
      # jem only handle one argument for now.
      for b in a:
        b = b.strip()
        if b.startswith('menu'):
          sidemenu = True
          r = re.compile(r'(?<!\\){(.*?)(?<!\\)}', re.M + re.S)
          g = re.findall(r, b)
          if len(g) > 3 or len(g) < 2:
            raise SyntaxError('sidemenu error on line %d' % f.linenum)

          if len(g) == 2:
            menu = (f, g[0], g[1], '')
          else:
            menu = (f, g[0], g[1], g[2])

        elif b.startswith('nofooter'):
          showfooter = False

        elif b.startswith('nodate'):
          showlastupdated = False

        elif b.startswith('notime'):
          showlastupdatedtime = False

        elif b.startswith('fwtitle'):
          fwtitle = True

        elif b.startswith('showsource'):
          showsourcelink = True

        elif b.startswith('nodefaultcss'):
          nodefaultcss = True

        elif b.startswith('addcss'):
          r = re.compile(r'(?<!\\){(.*?)(?<!\\)}', re.M + re.S)
          css += re.findall(r, b)

        elif b.startswith('addjs'):
          r = re.compile(r'(?<!\\){(.*?)(?<!\\)}', re.M + re.S)
          js += re.findall(r, b)

        elif b.startswith('addpackage'):
          r = re.compile(r'(?<!\\){(.*?)(?<!\\)}', re.M + re.S)
          f.eqpackages += re.findall(r, b)

        elif b.startswith('addtex'):
          r = re.compile(r'(?<!\\){(.*?)(?<!\\)}', re.M + re.S)
          f.texlines += re.findall(r, b)

        elif b.startswith('analytics'):
          r = re.compile(r'(?<!\\){(.*?)(?<!\\)}', re.M + re.S)
          f.analytics = re.findall(r, b)[0]

        elif b.startswith('title'):
          r = re.compile(r'(?<!\\){(.*?)(?<!\\)}', re.M + re.S)
          g = re.findall(r, b)
          if len(g) != 1:
            raise SyntaxError('addtitle error on line %d' % f.linenum)

          title = g[0]

        elif b.startswith('noeqs'):
          f.eqs = False

        elif b.startswith('noeqcache'):
          f.eqcache = False

        elif b.startswith('eqsize'):
          r = re.compile(r'(?<!\\){(.*?)(?<!\\)}', re.M + re.S)
          g = re.findall(r, b)
          if len(g) != 1:
            raise SyntaxError('eqsize error on line %d' % f.linenum)

          f.eqdpi = int(g[0])

        elif b.startswith('eqdir'):
          r = re.compile(r'(?<!\\){(.*?)(?<!\\)}', re.M + re.S)
          g = re.findall(r, b)
          if len(g) != 1:
            raise SyntaxError('eqdir error on line %d' % f.linenum)

          f.eqdir = g[0]

  # Get the file started with the firstbit.
  out(f.outf, f.conf['firstbit'])

  if not nodefaultcss:
    out(f.outf, f.conf['defaultcss'])

  # Add per-file css lines here.
  for i in range(len(css)):
    if '.css' not in css[i]:
      css[i] += '.css'

  for x in css:
    hb(f.outf, f.conf['specificcss'], x)

  for x in js:
    hb(f.outf, f.conf['specificjs'], x)

  # Look for a title.
  if pc(f) == '=': # don't check exact number f.outf '=' here jem.
    t = br(nl(f), f)[:-1]
    if title is None:
      title = re.sub(' *(<br />)|(&nbsp;) *', ' ', t)
  else:
    t = None

  #if title:
  hb(f.outf, f.conf['windowtitle'], title)

  out(f.outf, f.conf['bodystart'])


  if f.analytics:
    hb(f.outf, f.conf['analytics'], f.analytics)

  if fwtitle:
    out(f.outf, f.conf['fwtitlestart'])
    inserttitle(f, t)
    out(f.outf, f.conf['fwtitleend'])

  if menu:
    out(f.outf, f.conf['menustart'])
    insertmenuitems(*menu)
    out(f.outf, f.conf['menuend'])
  else:
    out(f.outf, f.conf['nomenu'])

  if not fwtitle:
    inserttitle(f, t)

  infoblock = False
  imgblock = False
  tableblock = False
  while 1: # wait for EOF.
    p = pc(f)

    if p == '':
      break

    elif p == '\\(':
      if not (f.eqs and f.eqsupport):
        break

      s = nl(f)
      # Quickly pull out the equation here:
      # Check we don't already have the terminating character in a whole-line
      # equation without linebreaks, eg \( Ax=b \):
      if not s.strip().endswith('\)'):
        while True:
          l = nl(f, codemode=True)
          if not l:
            break
          s += l
          if l.strip() == '\)':
            break
      r = br(s.strip(), f)
      r = myeqresub(r)
      out(f.outf, r)

    # look for lists.
    elif p == '-':
      dashlist(f, False)

    elif p == '.':
      dashlist(f, True)

    elif p == ':':
      colonlist(f)

    # look for titles.
    elif p == '=':
      (s, c) = nl(f, True)
      # trim trailing \n.
      s = s[:-1]
      hb(f.outf, '<h%d>|</h%d>\n' % (c, c), br(s, f))

    # look for comments.
    elif p == '#':
      l = nl(f)

    elif p == '\n':
      nl(f)

    # look for blocks.
    elif p == '~':
      nl(f)
      if infoblock:
        out(f.outf, f.conf['infoblockend'])
        infoblock = False
        nl(f)
        continue
      elif imgblock:
        out(f.outf, '</div></div></div></div>\n')
        imgblock = False
        nl(f)
        continue
      elif tableblock:
        out(f.outf, '</td></tr></table>\n')
        tableblock = False
        nl(f)
        continue
      else:
        if pc(f) == '{':
          l = allreplace(nl(f))
          r = re.compile(r'(?<!\\){(.*?)(?<!\\)}', re.M + re.S)
          g = re.findall(r, l)
        else:
          g = []

        # process jemdoc markup in titles.
        if len(g) >= 1:
          g[0] = br(g[0], f)

        if len(g) >= 2 and g[1] == 'table':
          # handles
          # {title}{table}{name}
          # one | two ||
          # three | four ||
          name = ''
          if len(g) >= 3 and g[2]:
            name += ' id="%s"' % g[2]
          out(f.outf, '<table class="table hovered bordered">\n<tr class="r1"><td class="c1">') # bordered, bordered, hovered
          f.tablerow = 1
          f.tablecol = 1

          tableblock = True

        elif len(g) >= 4 and (g[1] == 'img_left' or g[1] == 'img_center'):
          # handles
          # {}{img_left}{source}{alttext}{width}{height}{linktarget}.
          g += ['']*(7 - len(g))

          if g[4].isdigit():
            g[4] += 'px'

          if g[5].isdigit():
            g[5] += 'px'

          out(f.outf, '<div class="panel margin10 padding0"><div class="panel-content fg-dark">\n')
          out(f.outf, '<img src="%s"' % g[2])
          out(f.outf, ' alt="%s"' % g[3])
          if g[4]:
            out(f.outf, ' width="%s"' % g[4])
          if g[5]:
            out(f.outf, ' height="%s"' % g[5])
          if g[1] == 'img_left':
            out(f.outf, ' class="place-left margin10"/>')
          else:
            out(f.outf, ' class="place-center margin10"/>')
          out(f.outf, '<div class="page"><div class="page-content margin10 nlm nrm">')
          imgblock = True

        elif len(g) in (0, 1, 2): # info block.
          # handles
          # ~~~
          out(f.outf, f.conf['infoblockstart'])
          infoblock = True

        else:
          raise JandalError("couldn't handle block", f.linenum)

    else:
      s = br(np(f), f, tableblock)
      if s:
        if tableblock:
          hb(f.outf, '|\n', s)
        elif imgblock:
          hb(f.outf, '\n<p class="readable-text text-muted">|</p>\n', s)
        elif infoblock:
          #hb(f.outf, '\n<p class="code-text text-muted margin0 padding0">|</p>\n', s)
          hb(f.outf, '|\n', s)
        else:
          hb(f.outf, '\n<p class=readable-text>|</p>\n', s)

  if showfooter and (showlastupdated or showsourcelink):
    out(f.outf, f.conf['footerstart'])
    if showlastupdated:
      if showlastupdatedtime:
        ts = '%Y-%m-%d %H:%M:%S %Z'
      else:
        ts = '%Y-%m-%d'
      s = time.strftime(ts, time.localtime(time.time()))
      hb(f.outf, f.conf['lastupdated'], s)
    if showsourcelink:
      hb(f.outf, f.conf['sourcelink'], f.inname)
    out(f.outf, f.conf['footerend'])

  if menu:
    out(f.outf, f.conf['menulastbit'])
  else:
    out(f.outf, f.conf['nomenulastbit'])

  out(f.outf, f.conf['bodyend'])

  if f.outf is not sys.stdout:
    # jem: close file here.
    # jem: XXX this is where you would intervene to do a fast open/close.
    f.outf.close()

def main():
  if len(sys.argv) == 1 or sys.argv[1] in ('--help', '-h'):
    showhelp()
    raise SystemExit
  if sys.argv[1] == '--show-config':
    print standardconf()
    raise SystemExit
  if sys.argv[1] == '--version':
    info()
    raise SystemExit

  outoverride = False
  confoverride = False
  outname = None
  confnames = []
  for i in range(1, len(sys.argv), 2):
    if sys.argv[i] == '-o':
      if outoverride:
        raise RuntimeError("only one output file / directory, please")
      outname = sys.argv[i+1]
      outoverride = True
    elif sys.argv[i] == '-c':
      if confoverride:
        raise RuntimeError("only one config file, please")
      confnames.append(sys.argv[i+1])
      confoverride = True
    elif sys.argv[i].startswith('-'):
      raise RuntimeError('unrecognised argument %s, try --help' % sys.argv[i])
    else:
      break

  conf = parseconf(confnames)

  innames = []
  for j in range(i, len(sys.argv)):
    # First, if not a file and no dot, try opening .jemdoc. Otherwise, fall back
    # to just doing exactly as asked.
    inname = sys.argv[j]
    if not os.path.isfile(inname) and '.' not in inname:
      inname += '.jemdoc'

    innames.append(inname)

  if outname is not None and not os.path.isdir(outname) and len(innames) > 1:
    raise RuntimeError('cannot handle one outfile with multiple infiles')

  for inname in innames:
    if outname is None:
      thisout = re.sub(r'.jemdoc$', '', inname) + '.html'
    elif os.path.isdir(outname):
      # if directory, prepend directory to automatically generated name.
      thisout = outname + re.sub(r'.jemdoc$', '', inname) + '.html'
    else:
      thisout = outname

    infile = open(inname, 'rUb')
    outfile = open(thisout, 'w')

    f = controlstruct(infile, outfile, conf, inname)
    procfile(f)

#
if __name__ == '__main__':
  main()
