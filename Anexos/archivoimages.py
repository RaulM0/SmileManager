import os
import shutil
import random

# Carpetas originales
orig_train_images = "dataset/train/images"
orig_train_labels = "dataset/train/labels"
orig_val_images = "dataset/valid/images"
orig_val_labels = "dataset/valid/labels"

# Carpetas del subset
subset_train_images = "subset/train/images"
subset_train_labels = "subset/train/labels"
subset_val_images = "subset/val/images"
subset_val_labels = "subset/val/labels"

# Crear carpetas si no existen
os.makedirs(subset_train_images, exist_ok=True)
os.makedirs(subset_train_labels, exist_ok=True)
os.makedirs(subset_val_images, exist_ok=True)
os.makedirs(subset_val_labels, exist_ok=True)

# Tomar 80 imágenes aleatorias de train
train_files_all = [f for f in os.listdir(orig_train_images) if f.lower().endswith(".jpg")]
train_files = random.sample(train_files_all, 80)

for f in train_files:
    shutil.copy(os.path.join(orig_train_images, f), subset_train_images)
    shutil.copy(os.path.join(orig_train_labels, f.replace(".jpg", ".txt")), subset_train_labels)

# Tomar 20 imágenes aleatorias de valid
val_files_all = [f for f in os.listdir(orig_val_images) if f.lower().endswith(".jpg")]
val_files = random.sample(val_files_all, 20)

for f in val_files:
    shutil.copy(os.path.join(orig_val_images, f), subset_val_images)
    shutil.copy(os.path.join(orig_val_labels, f.replace(".jpg", ".txt")), subset_val_labels)

print("Subset de 100 imágenes preparado correctamente (80 train + 20 val).")
