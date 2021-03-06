lana
====

A toolbox to analyze lymphocyte tracks within lymphnodes from microscopy or simulations. It is based on [Pandas](http://pandas.pydata.org/), [numpy](http://www.numpy.org/), [matplotlib](http://matplotlib.org/), [seaborn](http://web.stanford.edu/~mwaskom/software/seaborn/), [statsmodels](http://statsmodels.sourceforge.net/), [scikit-learn](http://scikit-learn.org/) and [scikit-image](http://scikit-image.org/) and produces figures like the following motility analysis:

![alt text](motility.png "Motility plot")


Modules
-------
  * **motility.py**: Tools to analyze cell motility from positions within lymph nodes.
  * **remix.py**: Statistical models to generate tracks based on data.
  * **contacts.py**: Simulate contacts between T cells and dendritic cells.
  * **imaris.py**: Loads cell tracks from excel spreadsheets exported from [Imaris](http://www.bitplane.com/imaris/imaris).
  * **volocity.py**: Loads [Volocity](http://www.perkinelmer.co.uk/volocity) cell tracks.
  * **spim.py**: Displays and finds cells in SPIM (Single Plane Illumination Microscopy) data.

To install the required packages run `$ pip install -r requirements.txt`. For usage see the examples in `if __name__ == '__main__'` in the corresponding `module.py`, which can be executed with `$ python -m lana.module`.
