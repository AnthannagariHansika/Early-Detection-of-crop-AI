import os
import shutil
import random

source = "dataset"
output = "dataset_split"

classes = [
    "Tomato_Early_blight_leaf",
    "Tomato_Healthy_leaf",
    "Tomato_leaf_late_blight",
    "Tomato_leaf_yellow_curl_virus",
    "Tomato_mold_leaf",
    "Tomato_Septoria_leaf_spot"
]

for split in ["train", "val", "test"]:
    for cls in classes:
        os.makedirs(os.path.join(output, split, cls), exist_ok=True)

for cls in classes:
    folder = os.path.join(source, cls)

    images = [
        f for f in os.listdir(folder)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    ]

    random.shuffle(images)

    total = len(images)
    train_end = int(total * 0.70)
    val_end = int(total * 0.85)

    train_images = images[:train_end]
    val_images = images[train_end:val_end]
    test_images = images[val_end:]

    for f in train_images:
        shutil.copy2(
            os.path.join(folder, f),
            os.path.join(output, "train", cls, f)
        )

    for f in val_images:
        shutil.copy2(
            os.path.join(folder, f),
            os.path.join(output, "val", cls, f)
        )

    for f in test_images:
        shutil.copy2(
            os.path.join(folder, f),
            os.path.join(output, "test", cls, f)
        )

    print(cls, ":", len(images), "images")

print("\nDataset preparation completed!")