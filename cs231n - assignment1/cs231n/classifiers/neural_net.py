from __future__ import print_function

from builtins import range
from builtins import object
import numpy as np
import matplotlib.pyplot as plt
from past.builtins import xrange

class TwoLayerNet(object):
    """
    A two-layer fully-connected neural network. The net has an input dimension of
    N, a hidden layer dimension of H, and performs classification over C classes.
    We train the network with a softmax loss function and L2 regularization on the
    weight matrices. The network uses a ReLU nonlinearity after the first fully
    connected layer.

    In other words, the network has the following architecture:

    input - fully connected layer - ReLU - fully connected layer - softmax

    The outputs of the second fully-connected layer are the scores for each class.
    """

    def __init__(self, input_size, hidden_size, output_size, std=1e-4):
        """
        Initialize the model. Weights are initialized to small random values and
        biases are initialized to zero. Weights and biases are stored in the
        variable self.params, which is a dictionary with the following keys:

        W1: First layer weights; has shape (D, H)
        b1: First layer biases; has shape (H,)
        W2: Second layer weights; has shape (H, C)
        b2: Second layer biases; has shape (C,)

        Inputs:
        - input_size: The dimension D of the input data.
        - hidden_size: The number of neurons H in the hidden layer.
        - output_size: The number of classes C.
        """
        self.params = {}
        self.params['W1'] = std * np.random.randn(input_size, hidden_size)
        self.params['b1'] = np.zeros(hidden_size)
        self.params['W2'] = std * np.random.randn(hidden_size, output_size)
        self.params['b2'] = np.zeros(output_size)

    def loss(self, X, y=None, reg=0.0):
        """
        Compute the loss and gradients for a two layer fully connected neural
        network.

        Inputs:
        - X: Input data of shape (N, D). Each X[i] is a training sample.
        - y: Vector of training labels. y[i] is the label for X[i], and each y[i] is
          an integer in the range 0 <= y[i] < C. This parameter is optional; if it
          is not passed then we only return scores, and if it is passed then we
          instead return the loss and gradients.
        - reg: Regularization strength.

        Returns:
        If y is None, return a matrix scores of shape (N, C) where scores[i, c] is
        the score for class c on input X[i].

        If y is not None, instead return a tuple of:
        - loss: Loss (data loss and regularization loss) for this batch of training
          samples.
        - grads: Dictionary mapping parameter names to gradients of those parameters
          with respect to the loss function; has the same keys as self.params.
        """
        # Unpack variables from the params dictionary
        W1, b1 = self.params['W1'], self.params['b1']
        W2, b2 = self.params['W2'], self.params['b2']
        N, D = X.shape

        # Compute the forward pass
        m1 = X @ W1                         # (N, H)
        bias1 = m1 + b1                     # (N, H)
        relu = (bias1 > 0) * bias1          # (N, H)
        m2 = relu @ W2                      # (N, C)
        bias2 = m2 + b2                     # (N, C)
        scores = bias2                      # (N, C)

        # If the targets are not given then jump out, we're done
        if y is None:
            return scores

        # Compute the loss
        scores = (scores.T - np.max(scores, axis=1)).T
        scores = np.math.e ** scores
        summation = np.sum(scores, axis=1)       # (N, )
        right_class_scores = scores[range(N), y]
        loss = (np.sum(np.log(summation) - np.log(right_class_scores))) / N + reg * (np.sum(W1 * W1) + np.sum(W2 * W2))

        # Backward pass: compute gradients
        scores = (scores.T / summation).T               # (N, C)
        scores[range(N), y] -= 1                        # (N, C)
        d_bias2 = scores / N                            # (N, C)
        d_b2 = np.sum(d_bias2, axis=0)                  # (C,)
        d_m2 = d_bias2                                  # (N, C)
        d_W2 = relu.T @ d_m2                            # (H, C)
        d_relu = d_m2 @ W2.T                            # (N, H)
        d_bias1 = (relu > 0) * d_relu                   # (N, H)
        d_b1 = np.sum(d_bias1, axis=0)                  # (H,)
        d_m1 = d_bias1                                  # (N, H)
        d_X = d_m1 @ W1.T                               # (N, D)
        d_W1 = X.T @ d_m1                               # (D, H)

        d_W1 += 2 * reg * W1
        d_W2 += 2 * reg * W2
        d_b1 += 2 * reg * b1
        d_b2 += 2 * reg * b2

        grads = {}
        grads['W1'] = d_W1
        grads['W2'] = d_W2
        grads['b1'] = d_b1
        grads['b2'] = d_b2

        return loss, grads

    def train(self, X, y, X_val, y_val,
              learning_rate=1e-3, learning_rate_decay=0.95,
              reg=5e-6, num_iters=100,
              batch_size=200, verbose=False):
        """
        Train this neural network using stochastic gradient descent.

        Inputs:
        - X: A numpy array of shape (N, D) giving training data.
        - y: A numpy array f shape (N,) giving training labels; y[i] = c means that
          X[i] has label c, where 0 <= c < C.
        - X_val: A numpy array of shape (N_val, D) giving validation data.
        - y_val: A numpy array of shape (N_val,) giving validation labels.
        - learning_rate: Scalar giving learning rate for optimization.
        - learning_rate_decay: Scalar giving factor used to decay the learning rate
          after each epoch.
        - reg: Scalar giving regularization strength.
        - num_iters: Number of steps to take when optimizing.
        - batch_size: Number of training examples to use per step.
        - verbose: boolean; if true print progress during optimization.
        """
        N = X.shape[0]
        iterations_per_epoch = max(N / batch_size, 1)

        # Use SGD to optimize the parameters in self.model
        loss_history = []
        train_acc_history = []
        val_acc_history = []

        for it in range(num_iters):
            
            # create a random batch of training data
            idx = np.random.choice(N, batch_size, replace=True)
            X_batch = X[idx, :]
            y_batch = y[idx]

            # compute loss and gradients using the current minibatch
            loss, grads = self.loss(X_batch, y=y_batch, reg=reg)
            loss_history.append(loss)

            # perform parameter update
            self.params['W1'] += - learning_rate * grads['W1']
            self.params['W2'] += - learning_rate * grads['W2']
            self.params['b1'] += - learning_rate * grads['b1']
            self.params['b2'] += - learning_rate * grads['b2']

            if verbose and it % 100 == 0:
                print('iteration %d / %d: loss %f' % (it, num_iters, loss))

            # Every epoch, check train and val accuracy and decay learning rate.
            if it % iterations_per_epoch == 0:
                # Check accuracy
                train_acc = (self.predict(X_batch) == y_batch).mean()
                val_acc = (self.predict(X_val) == y_val).mean()
                train_acc_history.append(train_acc)
                val_acc_history.append(val_acc)

                # Decay learning rate
                learning_rate *= learning_rate_decay

        return {
          'loss_history': loss_history,
          'train_acc_history': train_acc_history,
          'val_acc_history': val_acc_history,
        }

    def predict(self, X):
        """
        Use the trained weights of this two-layer network to predict labels for
        data points. For each data point we predict scores for each of the C
        classes, and assign each data point to the class with the highest score.

        Inputs:
        - X: A numpy array of shape (N, D) giving N D-dimensional data points to
          classify.

        Returns:
        - y_pred: A numpy array of shape (N,) giving predicted labels for each of
          the elements of X. For all i, y_pred[i] = c means that X[i] is predicted
          to have class c, where 0 <= c < C.
        """
        y_pred = np.argmax(self.loss(X), axis=1)

        return y_pred
