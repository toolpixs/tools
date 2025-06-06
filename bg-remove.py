 
from rembg import remove
from PIL import Image
import io

# Load the input image
input_path = "input_image.jpg"  # Replace with your image file path
output_path = "output_image.png"  # Output file path (PNG recommended for transparency)

# Open the image
with open(input_path, "rb") as input_file:
    input_image = input_file.read()

# Remove the background
output_image = remove(input_image)

# Save the output image
with open(output_path, "wb") as output_file:
    output_file.write(output_image)

print(f"Background removed! Saved as {output_path}")

 