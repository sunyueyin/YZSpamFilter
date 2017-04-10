# Embedded file name: /Users/michael/PycharmProjects/spamfilter/distance.py
import math as _math
import random

def chi2Q(x2, v, exp = _math.exp, min = min):
    """Return prob(chisq >= x2, with v degrees of freedom).
    
    v must be even.
    """
  #  raise v & 1 == 0 or AssertionError
    m = x2 / 2.0
    sum = term = exp(-m)
    for i in range(1, v // 2):
        term *= m / i
        sum += term

    return min(sum, 1.0)
