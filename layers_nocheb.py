import numpy as np
import tensorflow as tf
from tensorflow import keras


class GCN(keras.layers.Layer):

    def __init__(self, features, dropout=0, **kwargs):
        self.F_prime = features
        self.dropout = dropout

        super(GCN, self).__init__(**kwargs)

    def build(self, input_shape):
        # input is a tuple of tensors (A, X)
        self.w = self.add_weight(name="W_0",
                                 shape=(input_shape[1][1], self.F_prime),
                                 initializer=tf.initializers.GlorotUniform(),
                                 trainable=True)

        super(GCN, self).build(input_shape)

    def call(self, x):
        # input is a tuple (A, X)
        filtre = x[0]
        X = x[1]

        if self.dropout:
            X = tf.nn.dropout(X, rate=0.5)

        # do convolution
        hidden = tf.matmul(X, self.w)

        hidden = tf.matmul(filtre, hidden)

        return tf.tuple([filtre, tf.keras.activations.relu(hidden)])

    def compute_output_shape(self, input_shape):
        return (input_shape[0], self.F_prime)


class SimplePool(keras.layers.Layer):

    def __init__(self, mode, **kwargs):
        assert mode == "max" or mode == "mean", "GCNPool must have 'max' or 'mean' as mode"

        self.mode = mode

        super(SimplePool, self).__init__(**kwargs)

    def build(self, input_shape):
        # input is a tuple of tensors (A, X)

        super(SimplePool, self).build(input_shape)

    def call(self, x):
        # input is a tuple (A, X)
        filtre = x[0][0]
        X = x[0][1]
        node_indicator = x[1]

        if self.mode == "max":
            X = tf.math.segment_max(X, node_indicator)
        else:
            X = tf.math.segment_mean(X, node_indicator)

        return tf.tuple([filtre, X])

    def compute_output_shape(self, input_shape):
        return (input_shape[0] / self.in_size, self.F_prime)


class DiffPool(keras.layers.Layer):

    def __init__(self, max_clusters, **kwargs):
        self.max_clusters = max_clusters

        super(DiffPool, self).__init__(**kwargs)

    def build(self, input_shape):
        self.embed = GCN(features=input_shape[1][1])
        self.pool = GCN(features=self.max_clusters)

        self.batch_size = input_shape[1][0]

        super(DiffPool, self).build(input_shape)

    def call(self, x):
        # input is a tuple (A, X)
        filtre = x[0]
        X = x[1]
        node_indicator = x[2]

        (_, S) = self.pool(x)
        (_, Z) = self.embed(x)

        S = tf.keras.activations.softmax(S, axis=1)

        coarse_X = tf.matmul(S, Z, transpose_a=True)

        coarse_A = tf.matmul(filtre, S)
        coarse_A = tf.matmul(S, coarse_A, transpose_a=True)

        return tf.tuple([coarse_A, coarse_X])

    def compute_output_shape(self, input_shape):
        return (self.max_clusters, input_shape[1][2])


def convert_sparse_matrix_to_sparse_tensor(X):
    import tensorflow as tf

    coo = X.tocoo()
    indices = np.mat([coo.row, coo.col]).transpose()

    return tf.SparseTensor(indices, coo.data, coo.shape)