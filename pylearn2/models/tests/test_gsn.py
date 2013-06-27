#from pylearn2.costs.gsn import MSWalkbackReconstructionError as Cost
from pylearn2.costs.gsn import MBWalkbackCrossEntropy as Cost
#from pylearn2.costs.autoencoder import MeanSquaredReconstructionError as Cost

from pylearn2.corruption import GaussianCorruptor, SaltPepperCorruptor
from pylearn2.datasets.mnist import MNIST
from pylearn2.models.gsn import GSN
from pylearn2.termination_criteria import EpochCounter
from pylearn2.train import Train
from pylearn2.training_algorithms.sgd import SGD

HIDDEN_SIZE = 1500
SALT_PEPPER_NOISE = 0.4
GAUSSIAN_NOISE = 2

LEARNING_RATE = 0.25
MOMENTUM = 0.5

MAX_EPOCHS = 20
BATCHES_PER_EPOCH = 10

BATCH_SIZE = 32

dataset = MNIST(which_set='train')

# just 1 hidden layer
layers = [dataset.X.shape[1], HIDDEN_SIZE, HIDDEN_SIZE - 500]

vis_corruptor = SaltPepperCorruptor(SALT_PEPPER_NOISE)
pre_corruptor = GaussianCorruptor(GAUSSIAN_NOISE)
post_corruptor = GaussianCorruptor(GAUSSIAN_NOISE)

gsn = GSN.new(layers, vis_corruptor, pre_corruptor, post_corruptor)

def debug(walkback = 0):
    import numpy as np
    import theano
    T = theano.tensor
    F = theano.function

    check = lambda x: np.any(np.isnan(x)) or np.any(np.isinf(x))
    check_val = lambda x: np.all(x > 0.0) and np.all(x < 1.0)

    x = T.fmatrix()
    mb = dataset.X[:4, :]

    gsn._set_activations(x)
    data = F([x], gsn.activations)(mb)
    print "Activation shapes: ", data[0].shape, data[1].shape

    data = F([x], gsn.activations)(mb)
    print "STEP 0"
    for j in xrange(len(data)):
        print "Activation %d: " % j, data[j]
    print map(check, data)

    for time in xrange(1, len(gsn.aes) + walkback + 1):
        print ''
        gsn._update()
        data = F([x], gsn.activations)(mb)
        print "DATA GOOD: ", check_val(data[0])

        gsn._apply_postact_corruption(xrange(0, len(gsn.activations), 2))
        data = F([x], gsn.activations)(mb)

        print "STEP %d" % time
        if time > len(gsn.aes):
            print "WALKBACK %d" % (time - len(gsn.aes))

        for j in xrange(len(data)):
            print "Activation %d: " % j, data[j]

        print map(check, data)

def test():
    alg = SGD(LEARNING_RATE, init_momentum=MOMENTUM, cost=Cost(walkback=2),
              termination_criterion=EpochCounter(MAX_EPOCHS),
              batches_per_iter=BATCHES_PER_EPOCH, batch_size=BATCH_SIZE)

    trainer = Train(dataset, gsn, algorithm=alg)
    trainer.main_loop()
    print "done training"


if __name__ == '__main__':
    test()
