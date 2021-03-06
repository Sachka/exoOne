import collections
import functools
import itertools
import math
import random
from collections import defaultdict

# question 1

test = "src/sequoia-corpus.np_conll"


def split(filename, randomize=False, proportions=[("train", 8), ("dev", 1), ("test", 1)]):
    lines = []  # file lines
    sentences = collections.defaultdict(lambda: set())  # dict for sentence avg len
    in_sentence = False  # conll break
    sentence_count = 0  # nb sentr
    current_sentence = ""  # agglomerator
    current_sentence_len = 0  # agglomerator's len for sentence avg len
    with open(filename, "r") as f:  # read file
        lines = [l.strip() for l in f.readlines()]
    for line in lines:  # process file
        if len(line):
            if not in_sentence:
                in_sentence = True
                sentence_count += 1
            else:
                current_sentence += "\n"
            current_sentence += line
            current_sentence_len += 1
        else:
            in_sentence = False
            if sentence_count:
                sentences[current_sentence_len].add(current_sentence + "\n")
            current_sentence = ""
            current_sentence_len = 0
    if in_sentence and sentence_count:  # possible last sentence
        sentences[current_sentence_len].add(current_sentence + "\n")
    # sub corpora
    containers = [(set(), p[0], p[1]) for p in proportions]
    i = 0
    lengths = sentences.keys()
    max_index = sum([p[1] for p in proportions])

    def get_container(containers, current_idx):  # which corpus it should belong to
        prev = 0
        for c in containers:
            if i < (c[2] + prev):
                return c[0]
            prev += c[2]
    while sentence_count:  # splitting itself
        for length in lengths:
            current_sentences = [s for s in sentences[length]]
            if randomize:
                random.shuffle(current_sentences)
            for sentence in current_sentences:
                get_container(containers, i).add(sentence)
                sentence_count -= 1
                i += 1
                i %= max_index
    for container in containers:  # write
        with open(filename + "." + container[1], "w") as f:
            for sentence in container[0]:
                f.write(sentence)
    split_filenames = [(filename + "." + c[1], c[0]) for c in containers]
    return split_filenames

# question 2


conll_feature = collections.namedtuple("Feature", ["name", "value"])
conll_token = collections.namedtuple("conll_token", ["index", "form", "lemma", "pos", "xpos", "features", "head", "func"])


class conll_sentence:

    def __init__(self, raw_sentence):
        def __build_features(raw_string):
            return None if raw_string == '_' else tuple([conll_feature(t[0], t[1]) for t in [f.split("=") for f in raw_string.split("|")]])

        def __clean_cast(raw_string):
            return None if raw_string == '_' else raw_string
        self.tokens = tuple([conll_token(__clean_cast(tok[0]), __clean_cast(tok[1]), __clean_cast(tok[2]), __clean_cast(tok[3]), __clean_cast(
            tok[4]), __build_features(tok[5]), __clean_cast(tok[6]), __clean_cast(tok[7])) for tok in [raw_tok.split("\t") for raw_tok in raw_sentence.split("\n")]])

    def __repr__(self):
        return "conll_sentence(" + repr([t for t in self.tokens]) + ")"

    def as_data(self, features_func=None):
        return (((tok.pos, tok.form) for tok in self.tokens), len(self.tokens)) if features_func is None else features_func(self.tokens)

    def __str__(self):
        return self.__repr__()

    def __len__(self):
        return len(self.tokens)


class conll_corpus:

    def __init__(self, raw_sentences=None):
        self.sentences = [conll_sentence(raw_sentence) for raw_sentence in raw_sentences] if raw_sentences is not None else []

    def __repr__(self):
        return "conll_corpus(" + repr(self.sentences) + ")"

    def __str__(self):
        return self.__repr__()

    def __add__(self, other):
        new_corpus = conll_corpus()
        sentences_set = set(self.sentences)
        self.sentences.extend([s for s in other.sentences if s not in sentences_set])
        new_corpus.sentences = self.sentences
        return new_corpus

    def __len__(self):
        return len(self.sentences)

    def __get__item(self, idx):
        return self.sentences[idx]

    def as_data(self, features_func=None):
        return functools.reduce(lambda a, b: (itertools.chain(a[0], b[0]), a[1] + b[1]), map(lambda s: s.as_data(features_func=features_func), self.sentences))


def read_corpus(filename):
    current_sentence = ""
    sentences_set = set()
    with open(filename, "r") as f:
        lines = [l.strip() for l in f.readlines()]
    for line in lines:
        if len(line):
            current_sentence += line + "\n"
        elif len(current_sentence):
            sentences_set.add(current_sentence.strip())
            current_sentence = ""
    if len(current_sentence):
        sentences_set.add(current_sentence.strip())
    return conll_corpus(sentences_set)


# for it to run on repl.it ...


class SparseWeightVector:

    def __init__(self):

        self.weights = defaultdict(float)

    def __call__(self, x_key, y_key):
        """
        This returns the weight of a feature couple (x,y)
        Enables an  x = w('a','b') syntax.

        @param x_key: a tuple of observed values
        @param y_key: a string being a class name
        @return : the weight of this feature
        """
        return self.weights[(x_key, y_key)]

    def dot(self, xvec_keys, y_key):
        """
        This computes the dot product : w . Phi(x,y).
        Phi(x,y) is implicitly  generated by the function given (x,y)
        @param xvec_keys: a list (vector) of hashable x values
        @param y_key    : a y class name
        @return  w . Phi(x,y)
        """
        return sum([self.weights[(x_key, y_key)] for x_key in xvec_keys])

    @staticmethod
    def code_phi(xvec_keys, ykey):
        """
        Explictly generates a sparse boolean Phi(x,y) vector from (x,y) values
        @param xvec_keys:  a list of symbols
        @param ykey: a y class name
        Codes the vector x of symbolic tuples for class y on a sparse vector
        """
        w = SparseWeightVector()
        for xkey in xvec_keys:
            w[(xkey, ykey)] += 1.0
        return w

    def __getitem__(self, key):
        """
        This returns the weight of feature couple (x,y) given as value.
        Enables the 'x = w[]' syntax.

        @param key: a couple (x,y) of observed and class value
        @return : the weight of this feature
        """
        return self.weights[tuple(key)]

    def __setitem__(self, key, value):
        """
        This sets the weight of a feature couple (x,y) given as key.
        Enables the 'w[] = ' syntax.
        @param key:   a couple (x,y) of observed value and class value
        @param value: a real
        """
        self.weights[key] = value

    def __add__(self, other):

        weights = self.weights.copy()
        for key, value in other.weights.items():
            weights[key] += value
        w = SparseWeightVector()
        w.weights = weights
        return w

    def __sub__(self, other):

        weights = self.weights.copy()
        for key, value in other.weights.items():
            weights[key] -= value
        w = SparseWeightVector()
        w.weights = weights
        return w

    def __mul__(self, scalar):

        weights = self.weights.copy()
        for key, value in self.weights.items():
            weights[key] *= scalar
        w = SparseWeightVector()
        w.weights = weights
        return w

    def __rmul__(self, scalar):
        return self.__mul__(scalar)

    def __truediv__(self, scalar):
        weights = self.weights.copy()
        for key, value in self.weights.items():
            weights[key] /= scalar
        w = SparseWeightVector()
        w.weights = weights
        return w

    def __iadd__(self, other):
        """
        Sparse Vector inplace addition. Enables the '+=' operator.
        @param  other: a  SparseVectorModel object
        """
        for key, value in other.weights.items():
            self.weights[key] += value
        return self

    def __isub__(self, other):
        """
        Sparse Vector inplace substraction. Enables the '-=' operator.
        @param  other: a  SparseVectorModel object
        """
        for key, value in other.weights.items():
            self.weights[key] -= value
        return self

    def __neg__(self):
        """
        returns -w
        """
        w = SparseWeightVector()
        for key, value in self.weights.items():
            w.weights[key] = -value
        return w

    def load(self, istream):
        """
        Loads a model parameters from a text stream
        @param istream: an opened text stream
        """
        self.weights = defaultdict(int)
        for line in istream:
            fields = line.split()
            key, value = tuple(fields[:-1]), float(fields[-1])
            self.weights[key] = value

    def save(self, ostream):
        """
        Saves model parameters to a tesentencesxt stream
        @param ostream: an opened text output stream
                """
        for key, value in self.weights.items():
            print(' '.join(list(key) + [str(value)]), file=ostream)

    def __str__(self):
        """
        Pretty prints the weights vector on std output.
        May crash if vector is too wide/full
        """
        s = ''
        for key, value in self.weights.items():
            X, Y = key
            if isinstance(X, tuple):
                s += 'phi(%s,%s) = 1 : w = %f\n' % ('&'.join(X), Y, value)
            else:
                s += 'phi(%s,%s) = 1 : w = %f\n' % (X, Y, value)
        return s

# question 3


class AvgPerceptron:

    def __init__(self):
        self.weights = None
        self.classes = None
        self.__trained = False

    # default method for features selection (trigramm, bigram=R, bigramL)
    @staticmethod
    def _features_func(sentence):
        tokens = ['<line>'] + [t.form for t in sentence] + ['</line>']
        return zip([t.pos for t in sentence], zip(tokens, zip(tokens, tokens[1:], tokens[2:]), zip(tokens, tokens[1:]), zip(tokens[1:], tokens))), len(sentence)

    def train(self, train_corpus, dev_corpus, epochs=5, step=.1, features_func=lambda s: AvgPerceptron._features_func(s)):
        general_corpus, corpus_size = (train_corpus + dev_corpus).as_data(features_func=features_func)
        general_corpus = itertools.tee(general_corpus, epochs + 1)
        self.classes = list({d[0] for d in general_corpus[0]})
        weight_update = SparseWeightVector()
        self.weights = SparseWeightVector()
        mod = epochs * corpus_size
        for it in general_corpus[1:]:
            errors = False
            for gold, data in it:
                prediction = self.classify(data)
                if gold != prediction:
                    errors = True
                    weight_update += step * (SparseWeightVector.code_phi(data, gold) - SparseWeightVector.code_phi(data, prediction))
                    self.weights += (mod / (epochs * corpus_size)) * weight_update
                mod -= 1
                if not errors:
                    break
        self.__trained = True

    def predict(self, data):
        return [self.weights.dot(data, clazz) for clazz in self.classes]

    def classify(self, data):
        predictions = self.predict(data)
        return self.classes[predictions.index(max(predictions))]

    def test(self, test_corpus, features_func=lambda s: AvgPerceptron._features_func(s)):
        if not self.__trained:
            raise Exception("model was not trained")
        corpus, size = test_corpus.as_data(features_func=features_func)
        return sum([pos == self.classify(d) for pos, d in corpus]) / size


# split(test)
trainc = read_corpus(test + ".train")
devc = read_corpus(test + ".dev")
testc = read_corpus(test + ".test")
p = AvgPerceptron()
p.train(trainc, devc)
print(p.test(testc))
