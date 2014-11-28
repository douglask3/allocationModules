##	requires notedown and ipython notebook:
##
##		notedown
##		========
##		pip install notedown
##
##		iPython
##		=======
##		For ipython notebook, try:
##			pip install ipython all
##		If thats doesnt work:
##			pip install pyzmq
##			pip install tornado
##
## For more information about notedown and ipython, see:
## [notedown]: http://github.com/aaren/notedown
## [github]: https://github.com/aaren/notedown/blob/master/example.md
## [nbviewer]: http://nbviewer.ipython.org/github/aaren/notedown/blob/master/example.ipynb


rm *.pyc
notedown example.md > MaxWexample.ipynb
ipython notebook MaxWexample.ipynb
#ipython notebook --pylab inline
#ipython nbconvert --to=html --ExecutePreprocessor.enabled=True MaxWexample.ipynb