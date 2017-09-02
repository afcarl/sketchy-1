import argparse

import numpy as np

import torch

from spotlight.datasets.movielens import get_movielens_dataset
from spotlight.cross_validation import user_based_train_test_split

from sketchy.sequence import get_objective, hyperparameter_space
from sketchy.hyperparameters import optimize


CUDA = torch.cuda.is_available()


def load_data(dataset, random_state):

    dataset = get_movielens_dataset(dataset)

    max_sequence_length = int(np.percentile(dataset.tocsr()
                                            .getnnz(axis=1),
                                            95))
    min_sequence_length = 20
    step_size = max_sequence_length

    train_nonsequence, rest = user_based_train_test_split(dataset,
                                                          test_percentage=0.2,
                                                          random_state=random_state)
    test, validation = user_based_train_test_split(rest,
                                                   test_percentage=0.5,
                                                   random_state=random_state)

    train = train_nonsequence.to_sequence(max_sequence_length=max_sequence_length,
                                          min_sequence_length=min_sequence_length,
                                          step_size=step_size)
    test = test.to_sequence(max_sequence_length=max_sequence_length,
                            min_sequence_length=min_sequence_length,
                            step_size=step_size)
    validation = validation.to_sequence(max_sequence_length=max_sequence_length,
                                        min_sequence_length=min_sequence_length,
                                        step_size=step_size)

    return train_nonsequence, train, validation, test


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Run experiment.')
    parser.add_argument('dataset',
                        type=str,
                        help='Name of dataset to use')
    parser.add_argument('--num_trials',
                        default=10,
                        type=int,
                        help='Number of trials to run')

    args = parser.parse_args()

    random_state = np.random.RandomState(42)

    train_nonsequence, train, validation, test = load_data(args.dataset, random_state)

    objective = get_objective(train_nonsequence, train, validation, test)
    space = hyperparameter_space()

    fname = 'sequence_trials_{}.pickle'.format(args.dataset)

    for iteration in range(args.num_trials):
        print('Iteration {}'.format(iteration))
        trials = optimize(objective,
                          space,
                          trials_fname=fname,
                          max_evals=iteration + 1)

        print('Best trial: {}'.format(trials.best_trial))

        best_lsh_trial = sorted([x for x in trials.trials
                                 if x['misc']['vals']['lsh'][0] == 0],
                                key=lambda x: x['result']['loss'])

        if best_lsh_trial:
            print('Best LSH trial: {}'.format(best_lsh_trial[0]))
