MaxW Tests
==========
This is a series of tests of the python-coded MaxW
allocation and supporting production functions. Code
run using the following parameters should match the 
Mcad file provided by Ross McMurtie. See docs/Info
for original file.

First off, this currently needs setting up (hopefully I can remove
this but of code soon:

```python
import re
import sys
import argparse

from IPython.nbformat.v3.rwbase import NotebookReader
from IPython.nbformat.v3.nbjson import JSONWriter

import IPython.nbformat.v3.nbbase as nbbase
```

Parameter values
----------------
As defined by Mcad file
```python
from math import pi

## Photosynthesis & C balance
w       = 0.49          # C content of
Mastar  = 0.181         # Leaf mass per unit area at base of canopy (kg DM/m2)
Nf      = (14/w)*0.001  # Leaf N:C ratio (g N / g C)
Nabase  = Nf*Mastar*w   # Fix Narea at base of canopy (kg N/m2)
Kl      = 0.43          # Light extinction coefft
Ntot    = 21.6E-3       # Total canopy N content (kgN/m2) 
An      = 2.09E-3       # Slope of Amax vs Narea relationship (mol/kgN/s)
N0      = 4E-4          # Minimum N area for photosynthesis (kgN/m2)
alpha   = 0.06          # Quantum efficiency
Rleaf   = 0.0           # 0.09*2E-3Leaf maintenance respiration rate (mol/kgN/s)
I0      = 611E-6        # Incident photosynthetically active radiation (mol/m2/s),
CUE     = 0.45          # Using Mcad corrected values
Tauf    = 8             # Leaf lifespan (yrs)
Taur    = 1             # Root lifespan (yrs)

## Root & N uptake parameters
r0      = 0.017         # root radius (cm)
pr      = 0.38          # root tissue density (g/cm3)
Lr0     = 0.76678       # root length density at half max U /cm2
R0      = pi*r0**2*pr*Lr0*1000*w
                        # root mass density at half max kg C /m3
Umax1   = 0.012         # Annual supply of available soil N. aka Potential annual N uptake (gN/m2 ground/year)
Umax2   = 0.008     
D0      = 0.6           # Length scale for exponential decline (m)
Nr      = 0.015         # Root N:C ratio
                        # ~7E-3/w 
Nw      = 0.003         # Root N:C ratio
                        # ~1.5E-3/w 
Retrans = 0.5           # Fraction of leaf N retranslocated at senescence


## Conversion factors
Daysperyear = 209       # Growing season length (days)
Hoursperday = 14.14     # Daylight length (hrs)
Convfactor  = Daysperyear*Hoursperday*60*60*12*1E-3
                        # i.e seconds per year
```

Photosynthesis Equations
------------------------
```python
from photosythesis import photosythesis

ph=photosythesis(An,N0,Kl,Rleaf,I0,alpha,Convfactor)

print "Asat when na=0.003:"
print ph.Asat(0.003)

print "I0 when lai=0.0"
print ph.I(0.0)

print ph.Aa(0.0,0.003)
```




We create a new class `MarkdownReader` that inherits from
`NotebookReader`. The only requirement on this new class is that it
has a `.reads(self, s, **kwargs)` method that returns a notebook
JSON string.

We search for code blocks using regular expressions, making use of
named groups:

```python
fenced_regex = r"""
\n*                     # any number of newlines followed by
^(?P<fence>`{3,}|~{3,}) # a line starting with a fence of 3 or more ` or ~
(?P<language>           # followed by the group 'language',
[\w+-]*)                # a word of alphanumerics, _, - or +
[ ]*                    # followed by spaces
(?P<options>.*)         # followed by any text
\n                      # followed by a newline
(?P<content>            # start a group 'content'
[\s\S]*?)               # that includes anything
\n(?P=fence)$           # up until the same fence that we started with
\n*                     # followed by any number of newlines
"""

# indented code
indented_regex = r"""
\n*                        # any number of newlines
(?P<icontent>              # start group 'icontent'
(?P<indent>^([ ]{4,}|\t))  # an indent of at least four spaces or one tab
[\s\S]*?)                  # any code
\n*                        # any number of newlines
^(?!(?P=indent))           # stop when there is a line without at least
                            # the indent of the first one
"""

code_regex = r"({}|{})".format(fenced_regex, indented_regex)
code_pattern = re.compile(code_regex, re.MULTILINE | re.VERBOSE)
```

Then say we have some input text:

````python
text = u"""### Create IPython Notebooks from markdown

This is a simple tool to convert markdown with code into an IPython
Notebook.

Usage:

```
notedown input.md > output.ipynb
```


It is really simple and separates your markdown into code and not
code. Code goes into code cells, not-code goes into markdown cells.

Installation:

    pip install notedown
"""
````

We can parse out the code block matches with 

```python
code_matches = [m for m in code_pattern.finditer(text)]
```

Each of the matches has a `start()` and `end()` method telling us
the position in the string where each code block starts and
finishes. We use this and do some rearranging to get a list of all
of the blocks (text and code) in the order in which they appear in
the text:

```python
code = u'code'
markdown = u'markdown'
python = u'python'

def pre_process_code_block(block):
    """Preprocess the content of a code block, modifying the code
    block in place.

    Remove indentation and do magic with the cell language
    if applicable.
    """
    # homogenise content attribute of fenced and indented blocks
    block['content'] = block.get('content') or block['icontent']

    # dedent indented code blocks
    if 'indent' in block and block['indent']:
        indent = r"^" + block['indent']
        content = block['content'].splitlines()
        dedented = [re.sub(indent, '', line) for line in content]
        block['content'] = '\n'.join(dedented)

    # alternate descriptions for python code
    python_aliases = ['python', 'py', '', None]
    # ensure one identifier for python code
    if 'language' in block and block['language'] in python_aliases:
        block['language'] = python

    # add alternate language execution magic
    if 'language' in block and block['language'] != python:
        code_magic = "%%{}\n".format(block['language'])
        block['content'] = code_magic + block['content']

# determine where the limits of the non code bits are
# based on the code block edges
text_starts = [0] + [m.end() for m in code_matches]
text_stops = [m.start() for m in code_matches] + [len(text)]
text_limits = zip(text_starts, text_stops)

# list of the groups from the code blocks
code_blocks = [m.groupdict() for m in code_matches]
# update with a type field
code_blocks = [dict(d.items() + [('type', code)]) for d in
                                                            code_blocks]

# remove indents, add code magic, etc.
map(pre_process_code_block, code_blocks)

text_blocks = [{'content': text[i:j], 'type': markdown} for i, j
                                                   in text_limits]

# create a list of the right length
all_blocks = range(len(text_blocks) + len(code_blocks))

# cells must alternate in order
all_blocks[::2] = text_blocks
all_blocks[1::2] = code_blocks

# remove possible empty first, last text cells
all_blocks = [cell for cell in all_blocks if cell['content']]
```

Once we've done that it is easy to convert the blocks into IPython
notebook cells and create a new notebook:

```python
cells = []
for block in all_blocks:
    if block['type'] == code:
        kwargs = {'input': block['content'],
                  'language': block['language']}

        code_cell = nbbase.new_code_cell(**kwargs)
        cells.append(code_cell)

    elif block['type'] == markdown:
        kwargs = {'cell_type': block['type'],
                  'source': block['content']}

        markdown_cell = nbbase.new_text_cell(**kwargs)
        cells.append(markdown_cell)

    else:
        raise NotImplementedError("{} is not supported as a cell"
                                    "type".format(block['type']))

ws = nbbase.new_worksheet(cells=cells)
nb = nbbase.new_notebook(worksheets=[ws])
```

`JSONWriter` gives us nicely formatted JSON output:

```python
writer = JSONWriter()
print writer.writes(nb)
```
