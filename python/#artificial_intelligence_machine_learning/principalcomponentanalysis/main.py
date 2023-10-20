"""
PCA demo

Author: Sam Barba
Created 10/11/2021
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


plt.rcParams['figure.figsize'] = (7, 7)
plt.rcParams['mathtext.fontset'] = 'custom'
plt.rcParams['mathtext.it'] = 'Times New Roman:italic'
pd.set_option('display.max_columns', 12)
pd.set_option('display.width', None)


def load_data(path):
	df = pd.read_csv(path)
	print(f'\nRaw data:\n{df}')

	x, y = df.iloc[:, :-1], df.iloc[:, -1]
	x_to_encode = x.select_dtypes(exclude=np.number).columns
	labels = sorted(y.unique())

	for col in x_to_encode:
		if len(x[col].unique()) > 2:
			one_hot = pd.get_dummies(x[col], prefix=col)
			x = pd.concat([x, one_hot], axis=1).drop(col, axis=1)
		else:  # Binary feature
			x[col] = pd.get_dummies(x[col], drop_first=True)

	# Label encode y (for plotting with later)
	y = y.astype('category').cat.codes.to_frame()
	y.columns = ['classification']

	print(f'\nCleaned data:\n{pd.concat([x, y], axis=1)}')

	x, y = x.to_numpy().astype(float), y.squeeze().to_numpy().astype(int)
	x = (x - x.min(axis=0)) / (x.max(axis=0) - x.min(axis=0))  # Normalise (PCA sensitive to feature scaling)

	return x, y, labels


def transform(x, n_components):
	x -= x.mean(axis=0)

	covariance = np.cov(x.T)
	eigenvalues, eigenvectors = np.linalg.eig(covariance)

	indices = eigenvalues.argsort()[::-1]
	eigenvalues = eigenvalues[indices]
	eigenvectors = eigenvectors.T[indices]

	components = eigenvectors[:n_components]
	x_transform = x.dot(components.T)

	variability = covariance.trace()
	total_explained_variance = (eigenvalues / variability)[:n_components].sum()

	return x_transform, total_explained_variance


if __name__ == '__main__':
	choice = input(
		'\nEnter 1 to use banknote dataset,'
		'\n2 for breast tumour dataset,'
		'\n3 for iris dataset,'
		'\n4 for pulsar dataset,'
		'\n5 for Titanic dataset,'
		'\nor 6 for wine dataset\n>>> '
	)

	match choice:
		case '1': path = r'C:\Users\Sam\Desktop\Projects\datasets\banknoteData.csv'
		case '2': path = r'C:\Users\Sam\Desktop\Projects\datasets\breastTumourData.csv'
		case '3': path = r'C:\Users\Sam\Desktop\Projects\datasets\irisData.csv'
		case '4': path = r'C:\Users\Sam\Desktop\Projects\datasets\pulsarData.csv'
		case '5': path = r'C:\Users\Sam\Desktop\Projects\datasets\titanicData.csv'
		case _: path = r'C:\Users\Sam\Desktop\Projects\datasets\wineData.csv'

	choice = input('\nEnter no. components (2 or 3)\n>>> ')
	n_components = int(choice)
	if n_components not in (2, 3): n_components = 3

	x, y, labels = load_data(path)
	x_transform, explained_variance_ratio = transform(x, n_components)

	ax = plt.axes() if n_components == 2 else plt.axes(projection='3d')
	scatter = ax.scatter(*x_transform.T, c=y, alpha=0.5, cmap=plt.cm.brg) \
		if n_components == 2 else \
		ax.scatter3D(*x_transform.T, c=y, alpha=0.5, cmap=plt.cm.brg)
	ax.set_xlabel('Principal component 1')
	ax.set_ylabel('Principal component 2')
	if n_components == 3:
		x_plt, y_plt, z_plt = x_transform.T
		ax.plot(y_plt, z_plt, 'k.', markersize=2, alpha=0.4, zdir='x', zs=x_plt.min() - 0.1)
		ax.plot(x_plt, z_plt, 'k.', markersize=2, alpha=0.4, zdir='y', zs=y_plt.max() + 0.1)
		ax.plot(x_plt, y_plt, 'k.', markersize=2, alpha=0.4, zdir='z', zs=z_plt.min() - 0.1)
		ax.set_zlabel('Principal component 3')
	ax.set_title(fr'Shape of $x$: {x.shape}'
		f'\nShape of PCA transform: {x_transform.shape}'
		f'\nExplained variance ratio: {explained_variance_ratio:.4f}')
	handles, _ = scatter.legend_elements()
	for h in handles:
		h.set_alpha(1)
	ax.legend(handles, labels)
	# plt.savefig('pca.png')
	plt.show()
