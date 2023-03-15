"""
Naive Bayes classification demo

Author: Sam Barba
Created 21/11/2021
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix
from sklearn.metrics import ConfusionMatrixDisplay
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score

from naive_bayes_classifier import NaiveBayesClassifier


plt.rcParams['figure.figsize'] = (8, 5)
pd.set_option('display.max_columns', 12)
pd.set_option('display.width', None)


def load_data(path, train_test_ratio=0.8):
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

	# Label encode y
	y = y.astype('category').cat.codes.to_frame()
	y.columns = ['classification']

	print(f'\nCleaned data:\n{pd.concat([x, y], axis=1)}')

	x, y = x.to_numpy().astype(float), y.to_numpy().squeeze().astype(int)
	x_train, x_test, y_train, y_test = train_test_split(x, y, train_size=train_test_ratio, stratify=y)

	return x_train, y_train, x_test, y_test, labels


def plot_confusion_matrix(actual, predictions, labels, is_training):
	cm = confusion_matrix(actual, predictions)
	disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=labels)
	f1 = f1_score(actual, predictions, average='binary' if len(labels) == 2 else 'weighted')

	disp.plot(cmap=plt.cm.plasma)
	plt.title(f'{"Training" if is_training else "Test"} confusion matrix\n(F1 score: {f1})')
	plt.show()


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

	x_train, y_train, x_test, y_test, labels = load_data(path)

	clf = NaiveBayesClassifier()
	clf.fit(x_train, y_train)

	train_pred = np.array([clf.predict(i) for i in x_train])
	test_pred = np.array([clf.predict(i) for i in x_test])
	plot_confusion_matrix(y_train, train_pred, labels, True)
	plot_confusion_matrix(y_test, test_pred, labels, False)
