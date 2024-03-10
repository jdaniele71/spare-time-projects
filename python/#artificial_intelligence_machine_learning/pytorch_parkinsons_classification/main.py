"""
PyTorch classification of patient drawings for Parkinson's disease detection

Author: Sam Barba
Created 27/01/2024
"""

import os

import cv2 as cv
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay, f1_score, roc_curve
from sklearn.model_selection import train_test_split
import torch
from torch.utils.data import DataLoader
from tqdm import tqdm

from conv_net import CNN
from custom_dataset import CustomDataset
from early_stopping import EarlyStopping


np.random.seed(1)
pd.set_option('display.width', None)
pd.set_option('max_colwidth', None)
torch.manual_seed(1)

DATA_PATH = 'C:/Users/Sam/Desktop/Projects/datasets/parkinsons'  # Available from Kaggle
DATA_SUBFOLDERS = ['spiral_healthy', 'spiral_parkinsons', 'wave_healthy', 'wave_parkinsons']
INPUT_SIZE = 64
BATCH_SIZE = 256
N_EPOCHS = 100


def load_data(df):
	def preprocess_img(path, target_w_to_h=1):
		img = cv.imread(path)
		img = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
		img = cv.medianBlur(img, 3)  # De-noise
		_, img = cv.threshold(img, 200, 255, cv.THRESH_BINARY_INV)

		# Make img aspect ratio 1:1
		img_h, img_w = img.shape[:2]

		if img_w / img_h < target_w_to_h:
			# Extend width of image with black background
			new_w = img_h
			new_img = np.zeros((img_h, new_w), dtype=np.uint8)
			horiz_paste_pos = (new_w - img_w) // 2
			new_img[:, horiz_paste_pos:horiz_paste_pos + img_w] = img
		elif img_w / img_h > target_w_to_h:
			# Extend height of image with black background
			new_h = img_w
			new_img = np.zeros((new_h, img_w), dtype=np.uint8)
			vert_paste_pos = (new_h - img_h) // 2
			new_img[vert_paste_pos:vert_paste_pos + img_h] = img
		else:
			new_img = img.copy()

		# Dilate drawing so that resizing doesn't "damage" it later
		kernel = np.ones((4, 4), np.uint8)
		new_img = cv.dilate(new_img, kernel)

		new_img = cv.resize(new_img, (INPUT_SIZE, INPUT_SIZE), interpolation=cv.INTER_NEAREST)

		return new_img


	x = [
		preprocess_img(p) for p in
		tqdm(df['img_path'], desc='Preprocessing images', ascii=True)
	]
	y = pd.get_dummies(df['class'], prefix='class', drop_first=True).astype(int).to_numpy().squeeze()
	class_dict = {'healthy': 0, 'parkinsons': 1}

	x_augmented = []
	for idx, img in enumerate(x):
		x_augmented.append(cv.rotate(img, cv.ROTATE_90_CLOCKWISE))
		x_augmented.append(cv.rotate(img, cv.ROTATE_90_COUNTERCLOCKWISE))
		x_augmented.append(cv.rotate(img, cv.ROTATE_180))
		x_augmented.append(cv.flip(img, 0))
		x_augmented.append(cv.flip(img, 1))
		y = np.append(y, [class_dict[df['class'][idx]]] * 5)

	x.extend(x_augmented)
	x = [img.astype(np.float64) / 255 for img in x]  # Normalise to [0,1]
	x = [img.reshape(1, INPUT_SIZE, INPUT_SIZE) for img in x]  # Colour channels, H, W
	x = np.array(x)

	# Train:validation:test ratio of 0.7:0.2:0.1
	x_train_val, x_test, y_train_val, y_test = train_test_split(x, y, train_size=0.9, stratify=y, random_state=1)
	x_train, x_val, y_train, y_val = train_test_split(x_train_val, y_train_val, train_size=0.78, stratify=y_train_val, random_state=1)

	# Convert to tensors
	x_val, y_val, x_test, y_test = map(
		lambda arr: torch.from_numpy(arr).float(),
		[x_val, y_val, x_test, y_test]
	)

	train_set = CustomDataset(x_train, y_train)
	train_loader = DataLoader(train_set, batch_size=BATCH_SIZE, shuffle=False, num_workers=8)

	return train_loader, x_val, y_val, x_test, y_test


if __name__ == '__main__':
	# 1. Convert data to dataframe

	data = []
	for subfolder in DATA_SUBFOLDERS:
		directory = f'{DATA_PATH}/{subfolder}'
		class_name = subfolder.split('_')[1]
		for img_path in os.listdir(directory):
			data.append((f'{directory}/{img_path}', class_name))

	df = pd.DataFrame(data, columns=['img_path', 'class'])

	# 2. Plot some examples

	example_indices = [0, 52, 102, 154]
	_, axes = plt.subplots(nrows=2, ncols=2, figsize=(8, 5))
	plt.subplots_adjust(top=0.85, bottom=0, hspace=0.1, wspace=0.1)
	for idx, ax in zip(example_indices, axes.flatten()):
		sample = cv.imread(df['img_path'][idx])
		ax.imshow(sample)
		ax.axis('off')
		ax.set_title(df['class'][idx])
	plt.suptitle('Data samples', x=0.514, y=0.95)
	plt.show()

	# 3. Plot output feature (class) distributions

	unique_values_counts = df['class'].value_counts()
	plt.bar(unique_values_counts.index, unique_values_counts.values)
	plt.xlabel('Class')
	plt.ylabel('Count')
	plt.title('Class distribution')
	plt.show()

	# 4. Preprocess data for loading

	print(f'\nRaw data:\n{df}\n')

	train_loader, x_val, y_val, x_test, y_test = load_data(df)

	model = CNN()
	print(f'\nModel:\n{model}')

	loss_func = torch.nn.BCELoss()

	if os.path.exists('./model.pth'):
		model.load_state_dict(torch.load('./model.pth'))
	else:
		# 5. Train model

		print('\n----- TRAINING -----\n')

		optimiser = torch.optim.Adam(model.parameters(), lr=1e-4)
		early_stopping = EarlyStopping(patience=10, min_delta=0, mode='max')
		history = {'loss': [], 'F1': [], 'val_loss': [], 'val_F1': []}

		for epoch in range(1, N_EPOCHS + 1):
			total_loss = total_f1 = 0
			model.train()

			for x, y in train_loader:
				y_probs = model(x).squeeze()
				y_pred = y_probs.round().detach().numpy()

				loss = loss_func(y_probs, y)
				f1 = f1_score(y, y_pred)
				total_loss += loss.item()
				total_f1 += f1

				optimiser.zero_grad()
				loss.backward()
				optimiser.step()

			model.eval()
			with torch.inference_mode():
				y_val_probs = model(x_val).squeeze()
			y_val_pred = y_val_probs.round()
			val_loss = loss_func(y_val_probs, y_val).item()
			val_f1 = f1_score(y_val, y_val_pred)

			history['loss'].append(total_loss / len(train_loader))
			history['F1'].append(total_f1 / len(train_loader))
			history['val_loss'].append(val_loss)
			history['val_F1'].append(val_f1)

			print(f'Epoch {epoch}/{N_EPOCHS} | '
				f'Loss: {total_loss / len(train_loader)} | '
				f'F1: {total_f1 / len(train_loader)} | '
				f'Val loss: {val_loss} | '
				f'Val F1: {val_f1}')

			if early_stopping(val_f1, model.state_dict()):
				print('Early stopping at epoch', epoch)
				break

		model.load_state_dict(early_stopping.best_weights)  # Restore best weights
		torch.save(model.state_dict(), './model.pth')

		# Plot loss and F1 throughout training
		_, (ax_loss, ax_f1) = plt.subplots(nrows=2, sharex=True, figsize=(8, 5))
		ax_loss.plot(history['loss'], label='Training loss')
		ax_loss.plot(history['val_loss'], label='Validation loss')
		ax_f1.plot(history['F1'], label='Training F1')
		ax_f1.plot(history['val_F1'], label='Validation F1')
		ax_loss.set_ylabel('Binary\ncross-entropy')
		ax_f1.set_ylabel('F1')
		ax_f1.set_xlabel('Epoch')
		ax_loss.legend()
		ax_f1.legend()
		plt.title('Model loss and F1 score during training', y=2.24)
		plt.show()

	# 6. Testing

	print('\n----- TESTING -----\n')

	model.eval()
	with torch.inference_mode():
		test_pred_probs = model(x_test).squeeze()
	test_pred = test_pred_probs.round()
	test_loss = loss_func(test_pred_probs, y_test)
	print('Test loss:', test_loss.item())

	# Confusion matrix

	f1 = f1_score(y_test, test_pred)
	cm = confusion_matrix(y_test, test_pred)
	ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=['healthy', 'parkinsons']).plot(cmap='Blues')
	plt.title(f'Test confusion matrix\n(F1 score: {f1:.3f})')
	plt.show()

	# ROC curve

	fpr, tpr, _ = roc_curve(y_test, test_pred_probs)
	plt.plot([0, 1], [0, 1], color='grey', linestyle='--')
	plt.plot(fpr, tpr)
	plt.axis('scaled')
	plt.xlabel('False Positive Rate')
	plt.ylabel('True Positive Rate')
	plt.title('ROC curve')
	plt.show()