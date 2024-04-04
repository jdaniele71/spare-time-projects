"""
PyTorch neural network demo for binary classification, multiclass classification, or regression

Author: Sam Barba
Created 28/10/2022
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import f1_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import torch
from torch import nn

from _utils.csv_data_loader import load_csv_classification_data, load_csv_regression_data
from _utils.early_stopping import EarlyStopping
from _utils.model_architecture_plots import plot_model
from _utils.model_evaluation_plots import plot_confusion_matrix, plot_roc_curve


plt.rcParams['figure.figsize'] = (8, 5)
pd.set_option('display.max_columns', 12)
pd.set_option('display.width', None)
torch.manual_seed(1)

N_EPOCHS = 100


if __name__ == '__main__':
	task_choice = input(
		'\nEnter B for binary classification,'
		'\nM for multiclass classification,'
		'\nor R for regression\n>>> '
	).upper()
	print()

	match task_choice:
		case 'B':
			dataset_choice = input(
				'Enter 1 for banknote dataset,'
				'\n2 for breast tumour dataset,'
				'\n3 for mushroom dataset,'
				'\n4 for pulsar dataset,'
				'\nor 5 for Titanic dataset\n>>> '
			)
		case 'M':
			dataset_choice = input(
				'Enter G for glass dataset,'
				'\nI for iris dataset,'
				'\nor W for wine dataset\n>>> '
			).upper()
		case 'R':
			dataset_choice = input(
				'Enter B for Boston housing dataset,'
				'\nC for car value dataset,'
				'\nM for medical insurance dataset,'
				'\nor P for Parkinson\'s dataset\n>>> '
			).upper()
		case _:
			raise ValueError('Bad choice')

	match task_choice + dataset_choice:
		case 'B1': path = 'C:/Users/Sam/Desktop/projects/datasets/banknote_authentication.csv'
		case 'B2': path = 'C:/Users/Sam/Desktop/projects/datasets/breast_tumour_pathology.csv'
		case 'B3': path = 'C:/Users/Sam/Desktop/projects/datasets/mushroom_edibility_classification.csv'
		case 'B4': path = 'C:/Users/Sam/Desktop/projects/datasets/pulsar_identification.csv'
		case 'B5': path = 'C:/Users/Sam/Desktop/projects/datasets/titanic_survivals.csv'
		case 'MG': path = 'C:/Users/Sam/Desktop/projects/datasets/glass_classification.csv'
		case 'MI': path = 'C:/Users/Sam/Desktop/projects/datasets/iris_classification.csv'
		case 'MW': path = 'C:/Users/Sam/Desktop/projects/datasets/wine_classification.csv'
		case 'RB': path = 'C:/Users/Sam/Desktop/projects/datasets/boston_housing.csv'
		case 'RC': path = 'C:/Users/Sam/Desktop/projects/datasets/car_valuation.csv'
		case 'RM': path = 'C:/Users/Sam/Desktop/projects/datasets/medical_costs.csv'
		case 'RP': path = 'C:/Users/Sam/Desktop/projects/datasets/parkinsons_scale.csv'
		case _:
			raise ValueError('Bad choice')

	labels = None
	if task_choice in 'BM':
		x_train, y_train, x_val, y_val, x_test, y_test, labels, _ = \
			load_csv_classification_data(path, train_size=0.7, val_size=0.2, test_size=0.1, x_transform=StandardScaler(), one_hot_y=True, to_tensors=True)
	else:
		x_train, y_train, x_val, y_val, x_test, y_test, _ = \
			load_csv_regression_data(path, train_size=0.7, val_size=0.2, test_size=0.1, x_transform=StandardScaler(), to_tensors=True)

	# 1. Build model

	n_features = x_train.shape[1]
	n_targets = 1 if task_choice in 'BR' else len(y_train.unique(dim=0))

	match task_choice + dataset_choice:
		case 'B1' | 'B2' | 'B3' | 'B4':  # Banknote, breast tumour, mushroom, or pulsar dataset
			model = nn.Sequential(
				nn.Linear(in_features=n_features, out_features=8),
				nn.ReLU(),
				nn.Linear(8, n_targets),
				nn.Sigmoid()
			)
			optimiser = torch.optim.Adam(model.parameters(), lr=0.01)

		case 'B5':  # Titanic dataset
			model = nn.Sequential(
				nn.Linear(n_features, 8),
				nn.Dropout(0.1),
				nn.ReLU(),
				nn.Linear(8, n_targets),
				nn.Sigmoid()
			)
			optimiser = torch.optim.Adam(model.parameters(), lr=0.01)

		case 'MG' | 'MI':  # Glass or iris dataset
			model = nn.Sequential(
				nn.Linear(n_features, 64),
				nn.ReLU(),
				nn.Linear(64, 64),
				nn.ReLU(),
				nn.Linear(64, n_targets),
				nn.Softmax(dim=-1)
			)
			optimiser = torch.optim.Adam(model.parameters())  # LR = 1e-3

		case 'MW':  # Wine dataset
			model = nn.Sequential(
				nn.Linear(n_features, 16),
				nn.ReLU(),
				nn.Linear(16, n_targets),
				nn.Softmax(dim=-1)
			)
			optimiser = torch.optim.Adam(model.parameters(), lr=0.005)

		case 'RB':  # Boston housing dataset
			model = nn.Sequential(
				nn.Linear(n_features, 256),
				nn.Dropout(0.1),
				nn.ReLU(),
				nn.Linear(256, n_targets)  # Adding no activation function afterwards means linear activation
			)
			optimiser = torch.optim.RMSprop(model.parameters(), lr=1.5e-3)

		case 'RC':  # Car value dataset
			model = nn.Sequential(
				nn.Linear(n_features, 256),
				nn.ReLU(),
				nn.Linear(256, 256),
				nn.ReLU(),
				nn.Linear(256, n_targets)
			)
			optimiser = torch.optim.RMSprop(model.parameters(), lr=0.004)

		case _:  # Medical insurance or Parkinson's dataset
			model = nn.Sequential(
				nn.Linear(n_features, 4096),
				nn.ReLU(),
				nn.Linear(4096, n_targets)
			)
			optimiser = torch.optim.RMSprop(model.parameters(), lr=0.02)

	# print(model.state_dict())  # Model weights
	print(f'Model:\n{model}')
	plot_model(model, (n_features,))

	# 2. Training

	print('\n----- TRAINING -----\n')

	if task_choice == 'B':
		loss_func = nn.BCELoss()  # Binary cross-entropy
	elif task_choice == 'M':
		loss_func = nn.CrossEntropyLoss()  # Categorical cross-entropy
	else:
		loss_func = nn.MSELoss()  # Mean Squared Error
	mae_loss = nn.L1Loss()

	early_stopping = EarlyStopping(patience=10, min_delta=0, mode='min')
	history = {'loss': [], 'metric': [], 'val_loss': [], 'val_metric': []}

	for epoch in range(1, N_EPOCHS + 1):
		model.train()  # Set to training mode (required for layers such as dropout or batch norm)

		# Loss = cross-entropy for classification, MSE for regression
		# Metric = F1 score for classification, MAE for regression
		loss = metric = val_loss = val_metric = 0

		if task_choice == 'B':
			# Forward pass
			y_train_probs = model(x_train).squeeze()  # Class probabilities
			y_train_pred = y_train_probs.round().detach().numpy()  # Class predictions

			# Calculate loss and F1
			loss = loss_func(y_train_probs, y_train)  # If using BCEWithLogitsLoss, take raw logits instead of y_train_probs
			metric = f1_score(y_train, y_train_pred)  # Equivalent to a TensorFlow metric

			optimiser.zero_grad()  # Reset gradients from last step
			loss.backward()        # Backpropagation (calculate gradients with respect to all model params)
			optimiser.step()       # Gradient descent (update model params to reduce gradients)

			model.eval()  # Set to testing mode
			with torch.inference_mode():
				y_val_probs = model(x_val).squeeze()
			y_val_pred = y_val_probs.round()
			val_loss = loss_func(y_val_probs, y_val)
			val_metric = f1_score(y_val, y_val_pred)

		elif task_choice == 'M':
			y_train_probs = model(x_train).squeeze()
			y_train_pred = y_train_probs.argmax(dim=1)

			loss = loss_func(y_train_probs, y_train)
			metric = f1_score(y_train.argmax(dim=1), y_train_pred, average='weighted')

			optimiser.zero_grad()
			loss.backward()
			optimiser.step()

			model.eval()
			with torch.inference_mode():
				y_val_probs = model(x_val).squeeze()
			y_val_pred = y_val_probs.argmax(dim=1)
			val_loss = loss_func(y_val_probs, y_val)
			val_metric = f1_score(y_val.argmax(dim=1), y_val_pred, average='weighted')

		elif task_choice == 'R':
			y_train_pred = model(x_train).squeeze()

			loss = loss_func(y_train_pred, y_train)
			metric = mae_loss(y_train_pred, y_train)

			optimiser.zero_grad()
			loss.backward()
			optimiser.step()

			model.eval()
			with torch.inference_mode():
				y_val_pred = model(x_val).squeeze()
			val_loss = loss_func(y_val_pred, y_val).item()
			val_metric = mae_loss(y_val_pred, y_val)

		history['loss'].append(loss.item())
		history['metric'].append(metric if task_choice in 'BM' else metric.item())
		history['val_loss'].append(val_loss)
		history['val_metric'].append(val_metric if task_choice in 'BM' else val_metric.item())

		if epoch % 10 == 0:
			if task_choice in 'BM':
				print(f'Epoch: {epoch}  |  Loss: {loss}  |  F1: {metric}  |  Val loss: {val_loss}  |  Val F1: {val_metric}')
			else:
				print(f'Epoch: {epoch}  |  Loss: {loss}  |  MAE: {metric}  |  Val loss: {val_loss}  |  Val MAE: {val_metric}')

		if early_stopping(val_loss, model.state_dict()):
			print('Early stopping at epoch', epoch)
			break

	model.load_state_dict(early_stopping.best_weights)  # Restore best weights

	# Plot loss and F1/MAE throughout training

	_, (ax_loss, ax_metric) = plt.subplots(nrows=2, sharex=True)
	ax_loss.plot(history['loss'], label='Training loss')
	ax_loss.plot(history['val_loss'], label='Validation loss')
	ax_metric.plot(history['metric'], label='Training F1' if task_choice in 'BM' else 'Training MAE')
	ax_metric.plot(history['val_metric'], label='Validation F1' if task_choice in 'BM' else 'Validation MAE')
	ax_metric.set_xlabel('Epoch')
	ax_metric.set_ylabel('F1' if task_choice in 'BM' else 'MAE')
	if task_choice == 'B': ax_loss.set_ylabel('Binary\ncross-entropy')
	elif task_choice == 'M': ax_loss.set_ylabel('Categorical\ncross-entropy')
	else: ax_loss.set_ylabel('MSE')
	ax_loss.legend()
	ax_metric.legend()
	plt.suptitle(f'Loss and {"F1 score" if task_choice in "BM" else "MAE"} during training', y=0.95)
	plt.show()

	# 3. Testing

	print('\n----- TESTING -----\n')

	with torch.inference_mode():
		if task_choice == 'B':
			test_pred_probs = model(x_test).squeeze()
			test_pred_labels = test_pred_probs.round()

			test_loss = loss_func(test_pred_probs, y_test)
			print('Test loss:', test_loss.item())

			# Confusion matrix
			f1 = f1_score(y_test, test_pred_labels)
			plot_confusion_matrix(y_test, test_pred_labels, labels, f'Test confusion matrix\n(F1 score: {f1:.3f})')

			# ROC curve
			plot_roc_curve(y_test, test_pred_probs)

		elif task_choice == 'M':
			test_pred_probs = model(x_test).squeeze()
			test_pred_labels = test_pred_probs.argmax(dim=1)

			test_loss = loss_func(test_pred_probs, y_test)
			print('Test loss:', test_loss.item())

			# Confusion matrix
			f1 = f1_score(y_test.argmax(dim=1), test_pred_labels, average='weighted')
			plot_confusion_matrix(y_test.argmax(dim=1), test_pred_labels, labels, f'Test confusion matrix\n(F1 score: {f1:.3f})')

		else:
			test_pred_labels = model(x_test).squeeze()

			test_loss = loss_func(test_pred_labels, y_test)
			test_metric = mae_loss(test_pred_labels, y_test)

			print('Test loss:', test_loss.item())
			print('Test MAE:', test_metric.item())

	# To save/load a model:
	# torch.save(model.state_dict(), './model.pth')
	# model.load_state_dict(torch.load('./model.pth'))