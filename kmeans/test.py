import numpy as np
import matplotlib.pyplot as plt
from kmeans import kmeans

# Generate synthetic 2D data
#np.random.seed(42)
X = np.vstack([np.random.randn(100, 2) + np.array([3 * i, 3 * i]) for i in range(5)])
weights = np.ones(X.shape[0])

# Parameters
n_clusters = 5
max_iter = 100
alpha = 2
random_state = 42

# Run the custom K-means
centroids, labels = kmeans(X, weights, n_clusters, max_iter, alpha, random_state)

print(centroids)

# Plot the data points and centroids
plt.figure(figsize=(8, 6))
plt.scatter(X[:, 0], X[:, 1], c=labels, cmap='viridis', marker='o')
plt.scatter(centroids[:, 0], centroids[:, 1], s=300, c='red', marker='x')
plt.title('Custom K-means Clustering')
plt.xlabel('Feature 1')
plt.ylabel('Feature 2')
plt.show()
