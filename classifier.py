# Embedded file name: /Users/michael/PycharmProjects/spamfilter/classifier.py
import math
import re
import os
import sys
from distance import chi2Q
LN2 = math.log(2)

class WordInfo(object):
    __slots__ = ('spamcount', 'hamcount')

    def __init__(self):
        self.__setstate__((0, 0))

    def __repr__(self):
        return 'WordInfo' + repr((self.spamcount, self.hamcount))

    def __getstate__(self):
        return (self.spamcount, self.hamcount)

    def __setstate__(self, t):
        self.spamcount, self.hamcount = t


class classifier:
    WordInfoClass = WordInfo

    def __init__(self):
        self.wordinfo = {}
        self.probcache = {}
        self.nspam = self.nham = 0

    def getmodel(self):
        return self.__getstate__()

    def __getstate__(self):
        return (self.wordinfo, self.nspam, self.nham)

    def loadmodel(self, t):
        self.__setstate__(t)

    def __setstate__(self, t):
        self.wordinfo, self.nspam, self.nham = t[0:]
        self.probcache = {}

    def predict(self, wordstream, evidence = False):
        return int(self.chi2_spamprob(wordstream, evidence=False) * 100)

    def chi2_spamprob(self, wordstream, evidence = False):
        from math import frexp, log as ln
        H = S = 1.0
        Hexp = Sexp = 0
        clues = self._getclues(wordstream)
        for prob, word, record in clues:
            S *= 1.0 - prob
            H *= prob
            if S < 1e-200:
                S, e = frexp(S)
                Sexp += e
            if H < 1e-200:
                H, e = frexp(H)
                Hexp += e

        S = ln(S) + Sexp * LN2
        H = ln(H) + Hexp * LN2
        n = len(clues)
        if n:
            S = 1.0 - chi2Q(-2.0 * S, 2 * n)
            H = 1.0 - chi2Q(-2.0 * H, 2 * n)
            prob = (S - H + 1.0) / 2.0
        else:
            prob = 0.5
        if evidence:
            clues = [ (w, p) for p, w, _r in clues ]
            clues.sort(lambda a, b: cmp(a[1], b[1]))
            clues.insert(0, ('*S*', S))
            clues.insert(0, ('*H*', H))
            return (prob, clues)
        else:
            return prob

    def cover(self, wordstream, is_spam):
        self.learn(wordstream, is_spam)

    def learn(self, wordstream, is_spam):
        """Teach the classifier by example.
        
        wordstream is a word stream representing a message.  If is_spam is
        True, you're telling the classifier this message is definitely spam,
        else that it's definitely not spam.
        """
        self._add_msg(wordstream, is_spam)

    def discover(self, wordstream, is_spam):
        self.unlearn(wordstream, is_spam)

    def unlearn(self, wordstream, is_spam):
        """In case of pilot error, call unlearn ASAP after screwing up.
        
        Pass the same arguments you passed to learn().
        """
        self._remove_msg(wordstream, is_spam)

    def probability(self, record):
        """Compute, store, and return prob(msg is spam | msg contains word).
        
        This is the Graham calculation, but stripped of biases, and
        stripped of clamping into 0.01 thru 0.99.  The Bayesian
        adjustment following keeps them in a sane range, and one
        that naturally grows the more evidence there is to back up
        a probability.
        """
        spamcount = record.spamcount
        hamcount = record.hamcount
        try:
            return self.probcache[spamcount][hamcount]
        except KeyError:
            pass

        nham = float(self.nham or 1)
        nspam = float(self.nspam or 1)
        #raise Exception(hamcount <= nham or AssertionError('Token seen in more ham than ham trained.'))
        hamratio = hamcount / nham
        #raise Exception(spamcount <= nspam or AssertionError('Token seen in more spam than spam trained.'))
        spamratio = spamcount / nspam
        prob = spamratio / (hamratio + spamratio)
        S = 0.5
        StimesX = S * 0.45
        n = hamcount + spamcount
        prob = (StimesX + n * prob) / (S + n)
        try:
            self.probcache[spamcount][hamcount] = prob
        except KeyError:
            self.probcache[spamcount] = {hamcount: prob}

        return prob

    def _add_msg(self, wordstream, is_spam):
        self.probcache = {}
        if is_spam:
            self.nspam += 1
        else:
            self.nham += 1
        for word in set(wordstream):
            record = self._wordinfoget(word)
            if record is None:
                record = self.WordInfoClass()
            if is_spam:
                record.spamcount += 1
            else:
                record.hamcount += 1
            self._wordinfoset(word, record)

        self._post_training()
        return

    def _remove_msg(self, wordstream, is_spam):
        self.probcache = {}
        if is_spam:
            if self.nspam <= 0:
                raise ValueError('spam count would go negative!')
            self.nspam -= 1
        else:
            if self.nham <= 0:
                raise ValueError('non-spam count would go negative!')
            self.nham -= 1
        for word in set(wordstream):
            record = self._wordinfoget(word)
            if record is not None:
                if is_spam:
                    if record.spamcount > 0:
                        record.spamcount -= 1
                elif record.hamcount > 0:
                    record.hamcount -= 1
                if record.hamcount == 0 == record.spamcount:
                    self._wordinfodel(word)
                else:
                    self._wordinfoset(word, record)

        self._post_training()
        return

    def _post_training(self):
        """This is called after training on a wordstream.  Subclasses might
        want to ensure that their databases are in a consistent state at
        this point.  Introduced to fix bug #797890."""
        pass

    def _getclues(self, wordstream):
        mindist = 0.1
        clues = []
        push = clues.append
        for word in set(wordstream):
            tup = self._worddistanceget(word)
            if tup[0] >= mindist:
                push(tup)

        clues.sort()
        if len(clues) > 150:
            del clues[0:-150]
        return [ t[1:] for t in clues ]

    def _worddistanceget(self, word):
        record = self._wordinfoget(word)
        if record is None:
            prob = 0.5
        else:
            prob = self.probability(record)
        distance = abs(prob - 0.5)
        return (distance,
         prob,
         word,
         record)

    def _wordinfoget(self, word):
        return self.wordinfo.get(word)

    def _wordinfoset(self, word, record):
        self.wordinfo[word] = record

    def _wordinfodel(self, word):
        del self.wordinfo[word]


Bayes = classifier
Algorithm = Bayes()
