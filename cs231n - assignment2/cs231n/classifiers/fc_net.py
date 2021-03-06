from builtins import range
from builtins import object
import numpy as np

from cs231n.layers import *
from cs231n.layer_utils import *


class TwoLayerNet(object):
    """
    A two-layer fully-connected neural network with ReLU nonlinearity and
    softmax loss that uses a modular layer design. We assume an input dimension
    of D, a hidden dimension of H, and perform classification over C classes.

    The architecure should be affine - relu - affine - softmax.

    Note that this class does not implement gradient descent; instead, it
    will interact with a separate Solver object that is responsible for running
    optimization.

    The learnable parameters of the model are stored in the dictionary
    self.params that maps parameter names to numpy arrays.
    """

    def __init__(self, input_dim=3*32*32, hidden_dim=100, num_classes=10,
                 weight_scale=1e-3, reg=0.0):
        """
        Initialize a new network.

        Inputs:
        - input_dim: An integer giving the size of the input
        - hidden_dim: An integer giving the size of the hidden layer
        - num_classes: An integer giving the number of classes to classify
        - weight_scale: Scalar giving the standard deviation for random
          initialization of the weights.
        - reg: Scalar giving L2 regularization strength.
        """
        self.params = {}
        self.reg = reg

        self.params['W1'] = weight_scale * np.random.randn(input_dim, hidden_dim)
        self.params['W2'] = weight_scale * np.random.randn(hidden_dim, num_classes)
        self.params['b1'] = np.zeros(hidden_dim)
        self.params['b2'] = np.zeros(num_classes)

    def loss(self, X, y=None):
        """
        Compute loss and gradient for a minibatch of data.

        Inputs:
        - X: Array of input data of shape (N, d_1, ..., d_k)
        - y: Array of labels, of shape (N,). y[i] gives the label for X[i].

        Returns:
        If y is None, then run a test-time forward pass of the model and return:
        - scores: Array of shape (N, C) giving classification scores, where
          scores[i, c] is the classification score for X[i] and class c.

        If y is not None, then run a training-time forward and backward pass and
        return a tuple of:
        - loss: Scalar value giving the loss
        - grads: Dictionary with the same keys as self.params, mapping parameter
          names to gradients of the loss with respect to those parameters.
        """

        a1, a1cache = affine_forward(X, self.params['W1'], self.params['b1'])
        r1, r1cache = relu_forward(a1)
        scores, a2cache = affine_forward(r1, self.params['W2'], self.params['b2'])

        # If y is None then we are in test mode so just return scores
        if y is None:
            return scores

        loss, grads = 0, {}

        loss, dscores = softmax_loss(scores, y)
        loss += 0.5 * self.reg * \
            (np.sum(self.params['W1'] ** 2) + np.sum(self.params['W2'] ** 2))
        dr1, dw2, db2 = affine_backward(dscores, a2cache)
        da1 = relu_backward(dr1, r1cache)
        dx, dw1, db1 = affine_backward(da1, a1cache)
        dw1 += self.reg * self.params['W1']
        dw2 += self.reg * self.params['W2']

        grads['W1'] = dw1
        grads['W2'] = dw2
        grads['b1'] = db1
        grads['b2'] = db2

        return loss, grads


class FullyConnectedNet(object):
    """
    A fully-connected neural network with an arbitrary number of hidden layers,
    ReLU nonlinearities, and a softmax loss function. This will also implement
    dropout and batch/layer normalization as options. For a network with L layers,
    the architecture will be

    {affine - [batch/layer norm] - relu - [dropout]} x (L - 1) - affine - softmax

    where batch/layer normalization and dropout are optional, and the {...} block is
    repeated L - 1 times.

    Similar to the TwoLayerNet above, learnable parameters are stored in the
    self.params dictionary and will be learned using the Solver class.
    """

    def __init__(self, hidden_dims, input_dim=3*32*32, num_classes=10,
                 dropout=1, normalization=None, reg=0.0,
                 weight_scale=1e-2, dtype=np.float32, seed=None):
        """
        Initialize a new FullyConnectedNet.

        Inputs:
        - hidden_dims: A list of integers giving the size of each hidden layer.
        - input_dim: An integer giving the size of the input.
        - num_classes: An integer giving the number of classes to classify.
        - dropout: Scalar between 0 and 1 giving dropout strength. If dropout=1 then
          the network should not use dropout at all.
        - normalization: What type of normalization the network should use. Valid values
          are "batchnorm", "layernorm", or None for no normalization (the default).
        - reg: Scalar giving L2 regularization strength.
        - weight_scale: Scalar giving the standard deviation for random
          initialization of the weights.
        - dtype: A numpy datatype object; all computations will be performed using
          this datatype. float32 is faster but less accurate, so you should use
          float64 for numeric gradient checking.
        - seed: If not None, then pass this random seed to the dropout layers. This
          will make the dropout layers deteriminstic so we can gradient check the
          model.
        """
        self.normalization = normalization
        self.use_dropout = dropout != 1
        self.reg = reg
        self.num_layers = 1 + len(hidden_dims)
        self.dtype = dtype
        self.params = {}

        # Define all parameters of the neural net in self.params dictionary.
        # These parameters include "W" and "b" and in case we have normalization : "gamma" and "beta"
        dimensions = np.hstack((input_dim, hidden_dims, num_classes))

        for i in range(self.num_layers):
            self.params['W' + str(i + 1)] = weight_scale * np.random.randn(dimensions[i], dimensions[i + 1])
            self.params['b' + str(i + 1)] = np.zeros(dimensions[i + 1])

        if self.normalization != None:
            for i in range(len(hidden_dims)):
                self.params['gamma' + str(i + 1)] = np.ones(dimensions[i + 1])
                self.params['beta' + str(i + 1)] = np.zeros(dimensions[i + 1])

        # When using dropout we need to pass a dropout_param dictionary to each
        # dropout layer so that the layer knows the dropout probability and the mode
        # (train / test). You can pass the same dropout_param to each dropout layer.
        self.dropout_param = {}
        if self.use_dropout:
            self.dropout_param = {'mode': 'train', 'p': dropout}
            if seed is not None:
                self.dropout_param['seed'] = seed

        # With batch normalization we need to keep track of running means and
        # variances, so we need to pass a special bn_param object to each batch
        # normalization layer. You should pass self.bn_params[0] to the forward pass
        # of the first batch normalization layer, self.bn_params[1] to the forward
        # pass of the second batch normalization layer, etc.
        self.bn_params = []
        if self.normalization == 'batchnorm':
            self.bn_params = [{'mode': 'train'}
                              for i in range(self.num_layers - 1)]
        if self.normalization == 'layernorm':
            self.bn_params = [{} for i in range(self.num_layers - 1)]

        # Cast all parameters to the correct datatype
        for k, v in self.params.items():
            self.params[k] = v.astype(dtype)

    def loss(self, X, y=None):
        """
        Compute loss and gradient for the fully-connected net.

        Input / output: Same as TwoLayerNet above.
        """
        X = X.astype(self.dtype)
        mode = 'test' if y is None else 'train'

        # Set train/test mode for batchnorm params and dropout param since they
        # behave differently during training and testing.
        if self.use_dropout:
            self.dropout_param['mode'] = mode
        if self.normalization == 'batchnorm':
            for bn_param in self.bn_params:
                bn_param['mode'] = mode

        # Run forward pass to compute the scores of the classes.
        # The scores are saved in scores variable.
        # cache is a list of dictionaries. Each element is cache for the corresponding layer to be used in backward pass.
        out, cache = X, []
        for i in range(self.num_layers - 1):
            out, temp_cache = self._layer_forward(out, i)
            cache.append(temp_cache)
        temp_cache = {}
        out, temp_cache['affine'] = affine_forward(
            out, self.params['W' + str(self.num_layers)], self.params['b' + str(self.num_layers)])
        cache.append(temp_cache)
        scores = out

        # If test mode return early
        if mode == 'test':
            return scores

        # Run backward pass.
        loss, grads = 0.0, {}
        loss, dout = softmax_loss(scores, y)
        dout, dw, db = affine_backward(dout, cache[-1]['affine'])
        grads['W' + str(self.num_layers)] = dw + self.reg * self.params['W' + str(self.num_layers)]
        grads['b' + str(self.num_layers)] = db
        loss += 0.5 * self.reg * np.sum(self.params['W' + str(self.num_layers)] ** 2)
        for i in range(self.num_layers - 2, -1, -1):
            dout, dw, db, dgamma, dbeta = self._layer_backward(dout, cache[i])
            grads['W' + str(i + 1)] = dw + self.reg * self.params['W' + str(i + 1)]
            grads['b' + str(i + 1)] = db
            if self.normalization != None:
                grads['gamma' + str(i + 1)] = dgamma
                grads['beta' + str(i + 1)] = dbeta
            loss += 0.5 * self.reg * np.sum(self.params['W' + str(i + 1)] ** 2)

        return loss, grads

    def _layer_forward(self, x, layer_num):
        w = self.params['W' + str(layer_num + 1)]
        b = self.params['b' + str(layer_num + 1)]
        if self.normalization != None:
            gamma = self.params['gamma' + str(layer_num + 1)]
            beta = self.params['beta'+ str(layer_num + 1)]

        out = x
        cache = {}
        out, cache['affine'] = affine_forward(out, w, b)
        if self.normalization == 'batchnorm':
            out, cache['batchnorm'] = batchnorm_forward(out, gamma, beta, bn_param=self.bn_params[layer_num])
        elif self.normalization == 'layernorm':
            out, cache['layernorm'] = layernorm_forward(out, gamma, beta, ln_param=self.bn_params[layer_num])
        out, cache['relu'] = relu_forward(out)
        if self.use_dropout:
            out, cache['dropout'] = dropout_forward(out, self.dropout_param)
        return out, cache

    def _layer_backward(self, dout, cache):
        dgamma, dbeta = None, None
        
        if self.use_dropout:
            dout = dropout_backward(dout, cache['dropout'])
        dout = relu_backward(dout, cache['relu'])
        if self.normalization == 'batchnorm':
            dout, dgamma, dbeta = batchnorm_backward_alt(dout, cache['batchnorm'])
        elif self.normalization == 'layernorm':
            dout, dgamma, dbeta = layernorm_backward(dout, cache['layernorm'])
        dout, dw, db = affine_backward(dout, cache['affine'])

        return dout, dw, db, dgamma, dbeta
