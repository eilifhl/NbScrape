import requests
from PIL import Image
from io import BytesIO
import math
import os

# --- Configuration ---
# You need to adjust these values for the target image.
# We'll use the values found for 'URN:NBN:no-nb_digibok_2007080700052_0043'
IIIF_IMAGE_ID = 'URN:NBN:no-nb_digibok_2007080700052_0042'
FULL_WIDTH = 3184  # Found in the manifest for canvas _0043
FULL_HEIGHT = 4640 # Found in the manifest for canvas _0043
TILE_SIZE = 1024   # Found in the manifest's 'tiles' array
OUTPUT_FILENAME = f"stitched_{IIIF_IMAGE_ID}.jpg"
DOWNLOAD_DIR = "iiif_tiles"
# --- End Configuration ---

# The standard format of the NB.no image resolver URL
BASE_URL = "https://www.nb.no/services/image/resolver/"

def download_and_stitch_iiif_image(image_id, width, height, tile_size, output_file, download_dir):
    """
    Downloads tiles for a given IIIF image ID and stitches them together.
    """
    os.makedirs(download_dir, exist_ok=True)
    
    # Calculate the number of tiles in the grid
    cols = math.ceil(width / tile_size)
    rows = math.ceil(height / tile_size)
    
    print(f"Image dimensions: {width}x{height} pixels.")
    print(f"Tiling grid: {cols} columns x {rows} rows (total {cols*rows} tiles).")
    
    # Create an empty image for stitching
    stitched_image = Image.new('RGB', (width, height))
    
    # Loop through the grid rows and columns
    for row_idx in range(rows):
        for col_idx in range(cols):
            
            # --- 1. Calculate IIIF parameters ---
            
            # Top-left coordinate (x, y)
            x_start = col_idx * tile_size
            y_start = row_idx * tile_size
            
            # Actual tile width and height (handling edges)
            tile_w = min(tile_size, width - x_start)
            tile_h = min(tile_size, height - y_start)
            
            # IIIF Region parameter: {x},{y},{w},{h}
            region = f"{x_start},{y_start},{tile_w},{tile_h}"
            
            # IIIF Size parameter: {w}, (requesting full resolution for the tile)
            size = f"{tile_w},"
            
            # Construct the full IIIF URL
            # {identifier}/{region}/{size}/{rotation}/{quality}.{format}
            tile_url = f"{BASE_URL}{image_id}/{region}/{size}/0/default.jpg"
            
            # --- 2. Download the tile ---
            
            print(f"Downloading tile [{row_idx+1}/{rows}, {col_idx+1}/{cols}]: {region}")
            
            try:
                response = requests.get(tile_url, timeout=10)
                response.raise_for_status() # Raise exception for bad status codes (4xx or 5xx)

                # Save tile to a local file (optional, for debugging/reuse)
                tile_filename = os.path.join(download_dir, f"{image_id}_{col_idx}_{row_idx}.jpg")
                with open(tile_filename, 'wb') as f:
                    f.write(response.content)
                
                # Open the downloaded image data with Pillow
                tile_img = Image.open(BytesIO(response.content))
                
                # --- 3. Stitch the tile ---
                
                # Paste the tile into the final image at its calculated position
                stitched_image.paste(tile_img, (x_start, y_start))
                
            except requests.exceptions.RequestException as e:
                print(f"Error downloading {tile_url}: {e}")
                # You may want to skip this tile or insert a black square
                continue
    
    # --- 4. Save the final image ---
    
    print("\nStitching complete. Saving final image...")
    stitched_image.save(output_file)
    print(f"Success! Final image saved as: {output_file}")

if __name__ == '__main__':
    download_and_stitch_iiif_image(
        IIIF_IMAGE_ID,
        FULL_WIDTH,
        FULL_HEIGHT,
        TILE_SIZE,
        OUTPUT_FILENAME,
        DOWNLOAD_DIR
    )
