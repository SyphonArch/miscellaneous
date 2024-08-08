import numpy as np
import numba


@numba.njit(cache=True)
def kmeans(X, weights, n_clusters, max_iter=100, alpha=2, random_state=None):
    """K-means clustering with K-means++ initialization

    Parameters
    ----------
    X : array-like, shape (n_samples, n_features)
        The input data to cluster.
    weights : array-like, shape (n_samples,)
        The weight of each sample.
    n_clusters : int
        The number of clusters to form as well as the number of centroids to generate.
    max_iter : int, optional
        Maximum number of iterations of the k-means algorithm for a single run.
    alpha : float, optional
        The exponent of the distance weights.
    random_state : int, optional

    Returns
    -------
    centroids : array, shape (n_clusters, n_features)
        The estimated centroids.
    labels : array, shape (n_samples,)
        The label of each sample.
    """

    if random_state is not None:
        np.random.seed(random_state)

    n_samples, n_features = X.shape

    if np.all(weights == 0):
        weights = np.ones_like(weights)

    centroids = _kmeans_plusplus(X, weights, n_clusters, alpha)
    labels = np.zeros(n_samples, dtype=np.int64)

    for _ in range(max_iter):
        new_labels = np.argmin(_distance_from_points(X, centroids), axis=1)
        new_centroids = np.empty_like(centroids)

        for k in range(n_clusters):
            if np.any(new_labels == k):
                cluster_points = X[new_labels == k]
                cluster_weights = weights[new_labels == k]
                new_centroid = np.sum(cluster_points.T * cluster_weights, axis=1) / np.sum(cluster_weights)
                new_centroids[k] = new_centroid
            else:
                new_centroids[k] = X[np.random.randint(0, n_samples)]

        if np.allclose(centroids, new_centroids):
            break
        centroids = new_centroids
        labels = new_labels

    return centroids, labels


@numba.njit(cache=True)
def _kmeans_plusplus(X, weights, n_clusters, alpha):
    n_samples, n_features = X.shape
    n_local_trials = 2 + int(np.log(n_clusters))

    if np.all(weights == 0):
        weights = np.ones_like(weights)

    centroids = np.zeros((n_clusters, n_features), dtype=X.dtype)
    first_idx = np.random.randint(n_samples)
    centroids[0] = X[first_idx]

    distances = _distance_from_point(X, centroids[0])
    distances_alpha = distances ** alpha * weights

    for k in range(1, n_clusters):
        sum_distances_alpha = distances_alpha.sum()
        if sum_distances_alpha == 0:
            distances_alpha = np.ones_like(distances_alpha)
            sum_distances_alpha = distances_alpha.sum()

        probabilities = np.clip(distances_alpha / sum_distances_alpha, 0, 1)
        probabilities /= probabilities.sum()
        candidate_idxs = _numba_rand_choice(n_local_trials, probabilities)
        candidates = X[candidate_idxs]

        best_candidate_idx = candidates[
            np.argmin(np.sum(np.minimum(distances[:, None], _distance_from_points(X, candidates)), axis=0))]
        centroids[k] = best_candidate_idx
        new_distances = _distance_from_point(X, centroids[k])
        distances = np.minimum(distances, new_distances)
        distances_alpha = distances ** alpha * weights

    return centroids


@numba.njit(cache=True)
def _distance_from_point(X, point):
    return np.sqrt(np.sum(np.power(X - point, 2), axis=1))


@numba.njit(cache=True)
def _distance_from_points(X, points):
    n_samples = X.shape[0]
    n_points = points.shape[0]
    distances = np.empty((n_samples, n_points), dtype=X.dtype)
    for i in range(n_points):
        distances[:, i] = _distance_from_point(X, points[i])
    return distances


@numba.njit(cache=True)
def _numba_rand_choice(size, probabilities):  # assumes normalized probabilities
    """Numba-compatible implementation of np.random.choice

    Returns an array of indices drawn from the input probabilities.
    The range is inferred from the length of the probabilities array,
    i.e. the indices are in the range [0, len(probabilities)).

    Parameters
    ----------
    size : int
        The number of samples to draw.
        probabilities : array-like, shape (n_classes,)
        The probability of each class.
    Returns
    -------
        indices : array, shape (size,)
        The drawn samples.
    """
    p_cumsum = np.cumsum(probabilities)
    rands = np.random.rand(size)
    return np.searchsorted(p_cumsum, rands)

