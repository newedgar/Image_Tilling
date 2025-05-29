import cv2
from matplotlib.widgets import Button
import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# load every Element in the Yolo file into a list of polygons
def load_yolo_labels(label_file, img_width, img_height):
    polygons = []
    with open(label_file, 'r') as file:
        for line in file:
            parts = line.strip().split()
            class_id, *coords = map(float, parts)
            coords = [(coords[i] * img_width if i % 2 == 0 else coords[i] * img_height) for i in range(len(coords))]
            polygons.append(coords)
    return polygons


def show_image_with_polygons(image_path):
    global add_to_dataset
    add_to_dataset = False
    
    # get label path
    label_path = (os.path.splitext(image_path)[0] + ".txt").replace("/Image", "/Label")

    # Load image
    image = cv2.imread(image_path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    img_height, img_width, _ = image.shape

    # Load YOLO labels
    polygons = load_yolo_labels(label_path, img_width, img_height)

    # Plot image and polygons
    fig, ax = plt.subplots(1)
    ax.imshow(image)
    
    fig.set_size_inches(fig.get_size_inches()[0] * 2, fig.get_size_inches()[1] * 2)

    for polygon in polygons:
        polygon_points = [(polygon[i], polygon[i + 1]) for i in range(0, len(polygon), 2)]
        poly_patch = patches.Polygon(polygon_points, linewidth=2, edgecolor='r', facecolor='none')
        ax.add_patch(poly_patch)

    
    plt.show()



# Display a specific image with element polygons

image_path = "Exemple/Image/knllDXGrHBNBvDoeSOlprYZgKr53.1747332481231_small_70.png"

#show_image_with_polygons(image_path)