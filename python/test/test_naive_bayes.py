import shutil
import tempfile
import numpy as np
import scipy.sparse as sp

from nose.tools import assert_equal
from nose.tools import assert_true
from numpy.testing import assert_array_almost_equal

from sklearn.datasets import make_classification
from sklearn.naive_bayes import GaussianNB
from sklearn.naive_bayes import MultinomialNB

from common import SplearnTestCase
from splearn.rdd import ArrayRDD, DictRDD
from splearn.naive_bayes import SparkGaussianNB
from splearn.naive_bayes import SparkMultinomialNB


class NaiveBayesTestCase(SplearnTestCase):

    def setUp(self):
        super(NaiveBayesTestCase, self).setUp()
        self.outputdir = tempfile.mkdtemp()

    def tearDown(self):
        super(NaiveBayesTestCase, self).tearDown()
        shutil.rmtree(self.outputdir)

    def generate_dataset(self, classes, samples, blocks=None):
        X, y = make_classification(n_classes=classes,
                                   n_samples=samples, n_features=4,
                                   n_clusters_per_class=1,
                                   random_state=42)
        X = np.abs(X)

        X_rdd = self.sc.parallelize(X, 4)
        y_rdd = self.sc.parallelize(y, 4)

        Z = DictRDD(X_rdd.zip(y_rdd), columns=('X', 'y'), block_size=blocks)

        return X, y, Z


class TestGaussianNB(NaiveBayesTestCase):

    def test_same_prediction(self):
        X, y, Z = self.generate_dataset(2, 800000)

        local = GaussianNB()
        dist = SparkGaussianNB()

        local_model = local.fit(X, y)
        dist_model = dist.fit(Z, classes=np.unique(y))

        # TODO: investigate the variance further!
        assert_array_almost_equal(local_model.sigma_, dist_model.sigma_, 2)
        assert_array_almost_equal(local_model.theta_, dist_model.theta_, 6)


class TestMultinomialNB(NaiveBayesTestCase):

    def test_same_prediction(self):
        X, y, Z = self.generate_dataset(4, 100000)

        local = MultinomialNB()
        dist = SparkMultinomialNB()

        y_local = local.fit(X, y).predict(X)
        y_dist = dist.fit(Z, classes=np.unique(y)).predict(Z[:, 'X'])

        assert_array_almost_equal(y_local, np.concatenate(y_dist.collect()))


