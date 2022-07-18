"""constants.py
This module contains constants to be used throughout the code.
I'm storing them here to remove clutter from the main code.
"""

import inspect
import os
from pkg_resources import resource_filename


__ROOT__ = '/'.join(os.path.abspath(inspect.getfile(inspect.currentframe())
                                    ).split('/')[:-1])

masksdir = resource_filename('cerespp', 'masks')

# relevant lines
CaH = 3968.47
CaK = 3933.664
CaV = 3901
CaR = 4001
Ha = 6562.808
HeI = 5875.62
NaID1 = 5895.92
NaID2 = 5889.95

# Plotting
fontsize = 22
fontname = 'serif'
tick_labelsize = 18

# Exceptions
s_exceptions = ['fideos']
