"""
Decision tree regression demo

Author: Sam Barba
Created 19/10/2022
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from decision_tree import DecisionTree
from tree_plotter import plot_tree

plt.rcParams['figure.figsize'] = (8, 5)
pd.set_option('display.max_columns', 12)
pd.set_option('display.width', None)

def load_data(path, train_test_ratio=0.8):
	if path == 'sine':
		x = np.linspace(0, 2 * np.pi, 100).reshape(-1, 1)
		y = np.sin(x) + np.random.uniform(-0.1, 0.1, 100).reshape(-1, 1)
		x_train, x_test, y_train, y_test = train_test_split(x, y, train_size=train_test_ratio)
		return ['x'], x_train, y_train, x_test, y_test

	df = pd.read_csv(path)
	print(f'\nRaw data:\n{df}')

	x, y = df.iloc[:, :-1], df.iloc[:, -1]
	x_to_encode = x.select_dtypes(exclude=np.number).columns

	for col in x_to_encode:
		if len(x[col].unique()) > 2:
			one_hot = pd.get_dummies(x[col], prefix=col)
			x = pd.concat([x, one_hot], axis=1).drop(col, axis=1)
		else:  # Binary feature
			x[col] = pd.get_dummies(x[col], drop_first=True)
	features = x.columns

	print(f'\nCleaned data:\n{pd.concat([x, y], axis=1)}\n')

	x, y = x.to_numpy().astype(float), y.to_numpy().astype(float)
	x_train, x_test, y_train, y_test = train_test_split(x, y, train_size=train_test_ratio)

	return features, x_train, y_train, x_test, y_test

def make_best_tree(x_train, y_train, x_test, y_test):
	"""Test different max_depth values, and return tree with the best one"""

	best_tree = None
	best_mean_mse = np.inf

	# 0 max_depth means predicting all data points as the same value
	for max_depth in range(6):
		tree = DecisionTree(x_train, y_train, max_depth)
		train_mse = tree.evaluate(x_train, y_train)
		test_mse = tree.evaluate(x_test, y_test)
		mean_mse = (train_mse + test_mse) / 2
		print(f'max_depth {max_depth}: training MSE = {train_mse} | test MSE = {test_mse} | mean = {mean_mse}')

		if mean_mse < best_mean_mse:
			best_tree, best_mean_mse = tree, mean_mse
		else:
			break  # No improvement, so stop

		max_depth += 1

	return best_tree

if __name__ == '__main__':
	choice = input('\nEnter B to use Boston housing dataset,'
		+ '\nC for car value dataset,'
		+ '\nM for medical insurance dataset,'
		+ '\nor S for sine wave\n>>> ').upper()

	match choice:
		case 'B': path = r'C:\Users\Sam Barba\Desktop\Programs\datasets\bostonData.csv'
		case 'C': path = r'C:\Users\Sam Barba\Desktop\Programs\datasets\carValueData.csv'
		case 'M': path = r'C:\Users\Sam Barba\Desktop\Programs\datasets\medicalInsuranceData.csv'
		case _: path = 'sine'

	features, x_train, y_train, x_test, y_test = load_data(path)

	if path == 'sine':
		x = np.linspace(0, 2 * np.pi, 100)
		y = np.sin(x) + np.random.uniform(-0.1, 0.1, 100)

		plt.scatter(x, y, s=5, color='black', label='Data')
		for max_depth in [0, 1, 6]:
			tree = DecisionTree(x_train, y_train, max_depth)
			pred = [tree.predict([xi]) for xi in x]
			plt.plot(x, pred, label=f'Tree depth {tree.get_depth()}')
		plt.title('Sine wave prediction with different tree depths')
		plt.legend()
		plt.show()
	else:
		tree = make_best_tree(x_train, y_train, x_test, y_test)
		print(f'\nOptimal tree depth: {tree.get_depth()}')

	plot_tree(tree, features)