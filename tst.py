import networkx as nx

from helper import *
from layers import *

cheb = True


def main():
    batch_size = 2
    epochs = 1
    img_rows, img_cols = 3, 3

    A = make_full_adjacency(img_rows)
    A_hat = A + np.eye(img_rows * img_cols)

    G = nx.from_numpy_matrix(np.array(A))
    nx.draw(G, with_labels=True)
    # plt.show()

    A_hat = normalise_adjacency_matrix(A_hat)

    if cheb:
        filtres = chebyshev_polynomials(A_hat)
    else:
        filtres = [A_hat]
    batch_filtres = [batch_adjacency_matrix(i, batch_size) for i in filtres]

    X = np.ones(img_cols * img_rows * 2, dtype=np.float32).reshape(batch_size, img_cols * img_rows, 1)

    from tensorflow.keras.layers import Dense, LeakyReLU

    ###################################################

    test = GCN(batch_filtres, F_prime=2, input_shape=(img_cols * img_rows, 1))(X)
    test = LeakyReLU(alpha=0.3)(test)
    test = GCN(batch_filtres, F_prime=2)(test)
    test = LeakyReLU(alpha=0.3)(test)
    tf.print(test, summarize=-1)
    test = GCNPool(batch_size=2)(test)

    tf.print(test, summarize=-1)
    test = Dense(10, activation='softmax')(test)
    # tf.print(test, summarize=-1)

    ###################################################

    return


main()