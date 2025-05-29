import cv2
import os
import shutil
import random
from show_image import show_image_with_polygons

output_img_folder = "Output/Image/"  # Directory to save tiles
output_label_folder = "Output/Label/"  # Directory to save labels



def tile_image( image_path : str,tile_factor : int,  output_tag : str):
    image_name = os.path.basename(image_path).replace(".png","")

    # Load the image
    image = cv2.imread(image_path)
    height, width = image.shape[:2]

    # set or modify var given
    tile_size = int(width/tile_factor) 
    stride = int(tile_size/2)



    tile_count = 0
    for y_tile in range(0, height - tile_size + 1, stride):
        for x_tile in range(0, width - tile_size + 1, stride):
            # Define the tile's bounding box
            x_end_tile = x_tile + tile_size
            y_end_tile = y_tile + tile_size


            yolo_file_tiled = ""
            yolo_file = open("Output/"+image_name+"_pixel.txt", "r")

            # Check if hold is in the tile, if so, recenter hold origin to match new tile
            for line in yolo_file:
                if hold_in_tile(line, x_tile, y_tile,x_end_tile, y_end_tile):
                    yolo_file_tiled += new_hold_origin(line,x_tile,y_tile)

                

                
            #recenter hold for the tile
            if (yolo_file_tiled != ""):
                
                #save coord hold in file
                yolo_file_converted = convert_pixel_yolo_file_to_percent(yolo_file_tiled.splitlines(), tile_size, tile_size)
                with open(f'{output_label_folder}{image_name}_{output_tag}_{tile_count}.txt', 'w') as fp:
                    fp.write(yolo_file_converted)


                   
                # Extract the tile
                tile = image[y_tile:y_end_tile, x_tile:x_end_tile]

                # Save the tile as image
                tile_filename = f"{output_img_folder}{image_name}_{output_tag}_{tile_count}.png"
                cv2.imwrite(tile_filename, tile)
                tile_count += 1


    print(f"Created {tile_count} {output_tag} tiles")

# Function to check if a hold is within the tile, with at least 60% of its area inside the tile
def hold_in_tile(line: str, x_tile: int, y_tile: int,x_end_tile:int, y_end_tile: int) -> bool:
    number_hold_in_tile = 0

    coord = line.split(" ")
    for i in range(1,len(coord),2):
        if (x_tile <= float(coord[i]) <= x_end_tile) and (y_tile <= float(coord[i + 1]) <= y_end_tile): 
            number_hold_in_tile += 1

    if (number_hold_in_tile > int((len(coord)-1)/2) *0.6): #if 60% of the hold is in the tile
        return True
    else:
        return False
    

#Change the hold origin to fit the actual tile
def new_hold_origin(line, x_tile: int, y_tile: int) -> tuple:
    coord = line.split(" ")
    adjusted_coords = [coord[0]]  # Keep the class label as is (YOLO Format)
    for i in range(1, len(coord), 2):
        adjusted_x = float(coord[i]) - x_tile
        adjusted_y = float(coord[i + 1]) - y_tile
        adjusted_coords.append(str(adjusted_x))
        adjusted_coords.append(str(adjusted_y))

    return " ".join(adjusted_coords) +"\n"


# Convert YOLO format coordinates from percentage to pixel values
def convert_percent_yolo_file_to_pixel(file_path: str,  height: int, width: int):
    with open(file_path.replace(".png",".txt").replace("/Image","/Label"), "r") as infile, open("Output/" +os.path.basename(file_path).replace(".png","_pixel.txt").replace("/Image","/Label"), "w") as outfile:
        for line in infile:
            coord = line.split(" ")
            adjusted_coords = [coord[0]]  # Keep the class label as is (YOLO Format)
            for i in range(1, len(coord), 2):
                adjusted_x = float(coord[i]) * width
                adjusted_y = float(coord[i + 1]) * height
                adjusted_coords.append(str(adjusted_x))
                adjusted_coords.append(str(adjusted_y))
            outfile.write(" ".join(adjusted_coords) + "\n")


# Convert YOLO format coordinates from pixel values to percentage
def convert_pixel_yolo_file_to_percent(file_content: str, height: int, width: int):
    yolo_file = ""
    for line in file_content:
        class_label = line.split(" ")[0]  # Get the class label (first element)
        coord = line.split(" ")[1::]

        #move point outside the tile to the closest border
        for i in range(0, len(coord), 2):
            # if point outside
            if (float(coord[i]) < 0 or float(coord[i]) > width or float(coord[i + 1]) < 0 or float(coord[i + 1]) > height):
                # previous point is inside
                if point_is_inside_tile(i-2,i-1,width,height):
                    while not close_to_border(float(coord[i]),float(coord[i+1]),width,height):
                        # average coord between outside and inside to get the closest to border
                        coord[(i)%len(coord)] = str((float(coord[i])*15 + float(coord[(i+2)%len(coord)])) / 16)
                        coord[(i+1)%len(coord)] = str((float(coord[i+1])*15 + float(coord[(i+2+1)%len(coord)])) / 16)

                    
                # next point is inside
                elif point_is_inside_tile((i+2)%len(coord),(i+3)%len(coord),width,height):
                    while not close_to_border(float(coord[i]),float(coord[i+1]),width,height):
                        # average coord between outside and inside to get the closest to border
                        coord[(i)%len(coord)] = str((float(coord[i])*7 + float(coord[(i-2)%len(coord)])) / 16)
                        coord[(i+1)%len(coord)] = str((float(coord[i+1])*7 + float(coord[(i-2+1)%len(coord)])) / 16)



        # Convert pixel to percentage
        adjusted_coords = [class_label]
        for i in range(0, len(coord), 2):
            adjusted_x = clamp(float(coord[i]) / width)
            adjusted_y = clamp(float(coord[i + 1]) / height)
            adjusted_coords.append(f"{adjusted_x:.6f}")
            adjusted_coords.append(f"{adjusted_y:.6f}")

        yolo_file += " ".join(adjusted_coords) + "\n"

    return yolo_file


# Verify if a polygon's point is inside the tile
def point_is_inside_tile(x,y,width,height):
    return (float(x) >= 0 and float(x) <= width and float(y) >= 0 and float(y) <= height)


# if the point is enouth close to the interior border
# Return True
def close_to_border(x:float,y:float, width:int, height:int):
    # if point close enough to border: break
    if abs(x / width) < 0.01 or (x / width - 1) < 0.01 or (y / height) < 0.01 or (y / height - 1) < 0.01:
        return True
    else:
        return False


# Clamp function to restrict a value within a given range
def clamp(value: float) -> float:
    return max(0, min(value, 1))


# Start the tilling process, init folders, and launch one or multiple tiling
def tiling(image_path):
    print("########### Tiling Script started ###########")
    #remove last tiled images
    if os.path.exists("Output"):
        shutil.rmtree("Output")

    # Create output directory if it doesn't exist
    os.makedirs(output_img_folder, exist_ok=True)
    os.makedirs(output_label_folder, exist_ok=True)

    # Get the size of the image
    image = cv2.imread(image_path)
    image_height, image_width = image.shape[:2]


    convert_percent_yolo_file_to_pixel(image_path, image_height, image_width)

    #tile image with different sizes
    tile_image(image_path, int(5.5), "small")
    tile_image(image_path, int(3), "medium")
    tile_image(image_path, int(2), "big")


    print("########### Tiling Script ended ###########")
    

# Call the tiling function with the input image path
tiling("Input/Image/knllDXGrHBNBvDoeSOlprYZgKr53.1747332481231.png")  



# select a random file in tiled yolo file folder
def select_random_file() -> str:
    files = [f for f in os.listdir(output_img_folder) if os.path.isfile(os.path.join(output_img_folder, f))]
    if not files:
        raise ValueError("No files found in the folder")
    file_choosen = random.choice(files)
    return output_img_folder + file_choosen



#show 3 random tile
for i in range(3):
    show_image_with_polygons(select_random_file())
