"""Implements generic utilities for monitoring classes.

"""

import re


__author__ = "Ali Onur Uyar"
__copyright__ = "Copyright 2011, Ali Onur Uyar"
__credits__ = []
__license__ = "GPL"
__version__ = "0.9"
__maintainer__ = "Ali Onur Uyar"
__email__ = "aouyar at gmail.com"
__status__ = "Development"


def parse_value(val):
    """Parse input string and return int, float or str depending on format.
    
    @param val: Input string.
    @return:    Value of type int, float or str.
        
    """
    if re.match('-{0,1}\d+$',  str(val)):
            return int(val)
    elif re.match('-{0,1}\d*\.\d+$',  str(val)):
        return float(val)
    else:
        return val


class NestedDict(dict):
    
    def __getitem__(self, key):
        """x.__getitem__(y) <==> x[y]"""
        try:
            return dict.__getitem__(self, key)
        except KeyError:
            value = self[key] = type(self)()
            return value
        
    def set_nested(self, klist, value):
        """D.set_nested((k1, k2,k3, ...), v) -> D[k1][k2][k3] ... = v"""
        keys = list(klist)
        if len(keys) > 0:
            curr_dict = self
            last_key = keys.pop()
            for key in keys:
                if not curr_dict.has_key(key) or not isinstance(curr_dict[key], 
                                                                NestedDict):
                    curr_dict[key] = type(self)()
                curr_dict = curr_dict[key]
            curr_dict[last_key] = value
