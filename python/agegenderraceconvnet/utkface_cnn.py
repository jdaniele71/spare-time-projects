"""
VGG16-based CNN for age prediction and gender/race classification of UTKFace dataset

Author: Sam Barba
Created 22/10/2022
"""

# Reduce TensorFlow logger spam
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

from keras.applications.vgg16 import VGG16
from keras.layers import BatchNormalization, Dense, Dropout, Flatten
from keras.models import load_model, Model
from keras.utils.vis_utils import plot_model
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.optimizers import Adam

DATA_PATH = r'C:\Users\Sam Barba\Desktop\Programs\datasets\UTKFace'  # Available from Kaggle
BATCH_SIZE = 32
DATASET_DICT = {
	'race_id': {'0': 'white', '1': 'black', '2': 'asian', '3': 'indian', '4': 'other'},
	'gender_id': {'0': 'male', '1': 'female'}
}

plt.rcParams['figure.figsize'] = (9, 6)
pd.set_option('display.width', None)
pd.set_option('max_colwidth', None)

# ---------------------------------------------------------------------------------------------------- #
# --------------------------------------------  FUNCTIONS  ------------------------------------------- #
# ---------------------------------------------------------------------------------------------------- #

def clean_data(df):
	gender, race = df.pop('gender'), df.pop('race')

	gender = pd.get_dummies(gender, prefix='gender', drop_first=True)
	race_one_hot = pd.get_dummies(race, prefix='race')

	df = pd.concat([df, gender, race_one_hot], axis=1)
	return df

def make_model():
	vgg = VGG16(include_top=False, pooling='avg', input_shape=(128, 128, 3))
	for layer in vgg.layers[:-6]:
		layer.trainable = False

	vgg2 = Model(vgg.input, vgg.layers[-10].output)

	# Age branch
	flatten_age = Flatten()(vgg2.output)
	dense_age_1 = Dense(512, activation='relu')(flatten_age)
	batch_norm_age = BatchNormalization()(dense_age_1)
	dropout_age_1 = Dropout(0.5)(batch_norm_age)
	dense_age_2 = Dense(1024, activation='relu')(dropout_age_1)
	dropout_age_2 = Dropout(0.5)(dense_age_2)
	output_age = Dense(1, activation='linear', name='output_age')(dropout_age_2)

	# Gender branch
	flatten_gender = Flatten()(vgg2.output)
	dense_gender_1 = Dense(256, activation='relu')(flatten_gender)
	batch_norm_gender = BatchNormalization()(dense_gender_1)
	dropout_gender_1 = Dropout(0.5)(batch_norm_gender)
	dense_gender_2 = Dense(512, activation='relu')(dropout_gender_1)
	dropout_gender_2 = Dropout(0.5)(dense_gender_2)
	output_gender = Dense(1, activation='sigmoid', name='output_gender')(dropout_gender_2)

	# Race branch
	flatten_race = Flatten()(vgg2.output)
	dense_race_1 = Dense(256, activation='relu')(flatten_race)
	batch_norm_race = BatchNormalization()(dense_race_1)
	dropout_race_1 = Dropout(0.5)(batch_norm_race)
	dense_race_2 = Dense(512, activation='relu')(dropout_race_1)
	dropout_race_2 = Dropout(0.5)(dense_race_2)
	output_race = Dense(5, activation='softmax', name='output_race')(dropout_race_2)

	return Model(inputs=vgg.input, outputs=[output_age, output_gender, output_race])

def generate_splits(df):
	train_prop, val_prop = 0.8, 0.1  # Test proportion = 0.1
	train_size = int(df.shape[0] * train_prop)
	val_size = int(df.shape[0] * val_prop)

	perm = np.random.permutation(df.shape[0])
	train_idx = perm[:train_size]
	val_idx = perm[train_size:train_size + val_size]
	test_idx = perm[train_size + val_size:]

	return train_idx, val_idx, test_idx

def generate_images(*, df, idx, for_training):
	def preprocess_img(path):
		img = Image.open(path)
		img = img.resize((128, 128))
		img = np.array(img) / 255  # Scale from 0-1

		return img

	images, ages, races, genders = [], [], [], []

	while True:
		for i in idx:
			img = preprocess_img(df.iloc[i, 0])
			age = df.iloc[i, 1]
			gender = df.iloc[i, 2]
			race = df.iloc[i, 3:]

			images.append(img)
			ages.append(age)
			genders.append(gender)
			races.append(race)

			if len(images) >= BATCH_SIZE:
				yield np.array(images), [np.array(ages), np.array(genders), np.array(races, dtype=np.int32)]
				images, ages, genders, races = [], [], [], []

		if not for_training: break

# ---------------------------------------------------------------------------------------------------- #
# ----------------------------------------------  MAIN  ---------------------------------------------- #
# ---------------------------------------------------------------------------------------------------- #

def main():
	np.random.seed(1)

	# 1. Convert data to dataframe

	data = []
	for img_path in os.listdir(DATA_PATH):
		age, gender, race = img_path.split('_')[:3]
		age = int(age)
		gender = DATASET_DICT['gender_id'][gender]
		race = DATASET_DICT['race_id'][race]
		data.append((fr'{DATA_PATH}\{img_path}', age, gender, race))

	df = pd.DataFrame(data, columns=['img_path', 'age', 'gender', 'race'])

	# 2. Plot some examples

	rand_idx = np.random.choice(range(df.shape[0]), size=9, replace=False)
	_, axes = plt.subplots(nrows=3, ncols=3)
	plt.subplots_adjust(top=0.85, bottom=0.05, hspace=0.3, wspace=0)
	for idx, ax in enumerate(axes.flatten()):
		r = rand_idx[idx]
		sample = Image.open(df['img_path'][r])
		ax.imshow(sample)
		ax.set_xticks([])
		ax.set_yticks([])
		ax.set_title(f'{df["age"][r]}, {df["gender"][r]}, {df["race"][r]}')
	plt.suptitle('Data examples (age, gender, race)', x=0.508, y=0.95)
	plt.show()

	# 3. Plot output feature distributions

	fig, axes = plt.subplots(nrows=3)
	plt.subplots_adjust(hspace=0.4)
	for ax, col in zip(axes, ['age', 'gender', 'race']):
		unique_values, counts = np.unique(df[col].to_numpy(), return_counts=True)
		ax.bar(unique_values, counts)
		ax.set_xlabel(col.capitalize())
	fig.supylabel('Count')
	plt.suptitle('Output feature distributions', y=0.94)
	plt.show()

	# 4. Clean up data and create generators

	print(f'\nRaw data:\n{df}')
	df = clean_data(df)
	print(f'\nCleaned data:\n{df}')

	train_idx, val_idx, test_idx = generate_splits(df)
	train_gen = generate_images(df=df, idx=train_idx, for_training=True)
	val_gen = generate_images(df=df, idx=val_idx, for_training=True)
	test_gen = generate_images(df=df, idx=test_idx, for_training=False)

	choice = input('\nEnter T to train a new model or L to load existing one\n>>> ').upper()

	if choice == 'T':
		# 5. Create model

		model = make_model()
		print('\nModel summary:\n')
		model.summary()
		plot_model(model, show_shapes=True, expand_nested=True, show_layer_activations=True)

		model.compile(loss={
				'output_age': 'mean_squared_error',
				'output_gender': 'binary_crossentropy',
				'output_race': 'categorical_crossentropy'
			},
			loss_weights={
				'output_age': 0.1,
				'output_gender': 10,
				'output_race': 4
			},
			optimizer=Adam(learning_rate=1e-5),
			metrics={
				'output_age': 'mean_absolute_error',
				'output_gender': 'accuracy',
				'output_race': 'accuracy',
			}
		)

		# 6. Train model

		print('\n----- TRAINING -----\n')

		early_stopping = EarlyStopping(monitor='val_loss',
			min_delta=0,
			patience=10,
			restore_best_weights=True)

		history = model.fit(train_gen,
			epochs=50,
			steps_per_epoch=len(train_idx) // BATCH_SIZE,
			validation_data=val_gen,
			validation_steps=len(val_idx) // BATCH_SIZE,
			callbacks=[early_stopping],
			verbose=1)

		# Plot loss graphs
		_, axes = plt.subplots(nrows=3, sharex=True)
		plt.subplots_adjust(hspace=0.4)
		losses = [
			('Age', 'MSE', 'output_age_loss', 'val_output_age_loss'),
			('Gender', 'Binary\ncrossentropy', 'output_gender_loss', 'val_output_gender_loss'),
			('Race', 'Categorical\ncrossentropy', 'output_race_loss', 'val_output_race_loss')
		]
		for ax, (title, y_label, train_loss, val_loss) in zip(axes, losses):
			ax.plot(history.history[train_loss], label='Training')
			ax.plot(history.history[val_loss], label='Validation')
			ax.legend()
			ax.set_ylabel(y_label)
			ax.set_title(title)
		axes[-1].set_xlabel('Epoch')
		plt.suptitle('Loss during training')
		plt.savefig('loss.png')

		# Plot metrics graphs
		_, axes = plt.subplots(nrows=3, sharex=True)
		plt.subplots_adjust(hspace=0.4)
		metrics = [
			('Age', 'MAE', 'output_age_mean_absolute_error', 'val_output_age_mean_absolute_error'),
			('Gender', 'Accuracy', 'output_gender_accuracy', 'val_output_gender_accuracy'),
			('Race', 'Accuracy', 'output_race_accuracy', 'val_output_race_accuracy')
		]
		for ax, (title, y_label, train_met, val_met) in zip(axes, metrics):
			ax.plot(history.history[train_met], label='Training')
			ax.plot(history.history[val_met], label='Validation')
			ax.legend()
			ax.set_ylabel(y_label)
			ax.set_title(title)
		axes[-1].set_xlabel('Epoch')
		plt.suptitle('Metrics during training')
		plt.savefig('metrics.png')

		model.save('model.h5')
	elif choice == 'L':
		try:
			model = load_model('model.h5')
		except Exception as e:
			print(e)
			return
	else:
		return

	# 7. Evaluation

	print('\n----- EVALUATION -----\n')

	_, test_loss_age, test_loss_gender, test_loss_race, test_mae_age, test_acc_gender, test_acc_race = model.evaluate(test_gen)
	print('\nTest age loss (MSE):', test_loss_age)
	print('Test gender loss (binary crossentropy):', test_loss_gender)
	print('Test race loss (categorical crossentropy):', test_loss_race)
	print('Test age MAE:', test_mae_age)
	print('Test gender accuracy:', test_acc_gender)
	print('Test race accuracy:', test_acc_race)

	# Plot predictions of first 9 images of first test batch
	test_gen = generate_images(df=df, idx=test_idx, for_training=False)
	first_batch = next(test_gen)
	images, (ages, genders, races) = first_batch

	_, axes = plt.subplots(nrows=3, ncols=3)
	plt.subplots_adjust(top=0.8, bottom=0.05, hspace=0.5, wspace=0.4)
	for idx, ax in enumerate(axes.flatten()):
		age, gender, race = ages[idx], genders[idx], races[idx]

		# Subtract gender from 1, as model is predicting 'gender_male'.
		# If 'gender_male' = 1, the DATASET_DICT index should be 1 - 1 = 0
		# (it's 0 for male, 1 for female)
		gender = 1 - gender
		gender = DATASET_DICT['gender_id'][str(gender)]
		race = np.argmax(race)
		race = DATASET_DICT['race_id'][str(race)]

		img = images[idx]
		age_pred, gender_pred, race_pred = model.predict(np.expand_dims(img, 0))
		age_pred = round(age_pred[0][0])
		gender_pred = 1 - round(gender_pred[0][0])
		gender_pred = DATASET_DICT['gender_id'][str(gender_pred)]
		race_pred = np.argmax(race_pred[0])
		race_pred = DATASET_DICT['race_id'][str(race_pred)]

		ax.imshow(Image.fromarray((img * 255).astype(np.uint8)))
		ax.set_xticks([])
		ax.set_yticks([])
		ax.set_title(f'Predicted: {age_pred}, {gender_pred}, {race_pred}'
			+ f'\nActual: {age}, {gender}, {race}')

	plt.suptitle('Test output examples', x=0.508, y=0.95)
	plt.savefig('output_examples.png')
	plt.show()

if __name__ == '__main__':
	main()