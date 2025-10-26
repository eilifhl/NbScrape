import requests
from PIL import Image
from io import BytesIO
import math
import os
import json
from urllib.parse import urlparse, parse_qs

# --- Configuration ---
# Only the TILE_SIZE is fixed by NB.no's IIIF Image API implementation
TILE_SIZE = 1024
DOWNLOAD_DIR = "iiif_tiles"
BASE_IMAGE_RESOLVER_URL = "https://www.nb.no/services/image/resolver/"
# --- End Configuration ---

def get_params_from_url(url):
    """
    Extracts the Item ID and Page Number from the book's web URL.
    """
    parsed_url = urlparse(url)
    
    # 1. Extract Item ID (the part after /items/)
    try:
        item_id = parsed_url.path.split('/items/')[1].strip('/')
    except IndexError:
        raise ValueError(f"URL format is incorrect: Expected '/items/{{item_id}}', got '{parsed_url.path}'")

    # 2. Extract Page Number (from query string ?page=X)
    query_params = parse_qs(parsed_url.query)
    page_number = query_params.get('page', [''])[0]
    
    if not page_number:
        raise ValueError("URL must contain a '?page=X' query parameter.")
        
    return item_id, page_number

def get_iiif_details_from_manifest(item_id, page_label):
    """
    Downloads the IIIF Manifest and finds the details for the specific page.
    """
    manifest_url = f"https://api.nb.no/catalog/v1/iiif/{item_id}/manifest?profile=nbdigital"
    print(f"Fetching Manifest from: {manifest_url}")

    response = requests.get(manifest_url, timeout=15)
    response.raise_for_status()
    manifest = response.json()

    # Find the Canvas (page) that matches the requested page label
    for canvas in manifest.get('sequences', [{}])[0].get('canvases', []):
        if canvas.get('label') == page_label:
            # Found the correct page canvas
            
            # Extract Image Service details
            image_service = canvas.get('images', [{}])[0].get('resource', {}).get('service', {})
            
            iiif_id_url = image_service.get('@id')
            if not iiif_id_url:
                 raise KeyError("Could not find 'resource.service.@id' in the canvas object.")
            
            # The IIIF_IMAGE_ID is the last part of the service URL
            iiif_image_id = iiif_id_url.split('/')[-1]

            return {
                'id': iiif_image_id,
                'width': canvas['width'],
                'height': canvas['height']
            }
            
    raise ValueError(f"Page label '{page_label}' not found in the Manifest for item ID '{item_id}'.")


def download_and_stitch_iiif_image(image_id, width, height, tile_size, output_file, download_dir):
    # ... (The stitching logic from the previous response remains here)
    # The rest of the previous function is used here. 
    # For brevity in this response, I'm omitting the exact copy of the stitching loop,
    # but assume the function is identical to the one in the first answer.
    
    # NOTE: You must copy the full definition of this function from the previous 
    # answer into your script to make it runnable.
    
    # Placeholder for the actual logic:
    print(f"\nStitching will begin for ID: {image_id} ({width}x{height})")
    
    # Calculate the number of tiles in the grid
    cols = math.ceil(width / tile_size)
    rows = math.ceil(height / tile_size)
    
    print(f"Image dimensions: {width}x{height} pixels.")
    print(f"Tiling grid: {cols} columns x {rows} rows (total {cols*rows} tiles).")
    
    stitched_image = Image.new('RGB', (width, height))
    
    for row_idx in range(rows):
        for col_idx in range(cols):
            x_start = col_idx * tile_size
            y_start = row_idx * tile_size
            tile_w = min(tile_size, width - x_start)
            tile_h = min(tile_size, height - y_start)
            
            region = f"{x_start},{y_start},{tile_w},{tile_h}"
            size = f"{tile_w},"
            
            tile_url = f"{BASE_IMAGE_RESOLVER_URL}{image_id}/{region}/{size}/0/default.jpg"
            
            print(f"Downloading tile [{row_idx*cols + col_idx + 1}/{cols*rows}]: {region}")
            
            try:
                response = requests.get(tile_url, timeout=10)
                response.raise_for_status() 

                tile_img = Image.open(BytesIO(response.content))
                stitched_image.paste(tile_img, (x_start, y_start))
                
            except requests.exceptions.RequestException as e:
                print(f"Error downloading {tile_url}: {e}")
                continue
    
    print("\nStitching complete. Saving final image...")
    stitched_image.save(output_file)
    print(f"Success! Final image saved as: {output_file}")


if __name__ == '__main__':
    input_url = "https://www.nb.no/items/57638b8a5ed7c8f6e954edca1033df5f?page=41"

    try:
        item_id, page_label = get_params_from_url(input_url)
        print(f"Item ID: {item_id}, Target Page Label: {page_label}")
        
        iiif_details = get_iiif_details_from_manifest(item_id, page_label)
        
        IIIF_IMAGE_ID = iiif_details['id']
        FULL_WIDTH = iiif_details['width']
        FULL_HEIGHT = iiif_details['height']
        OUTPUT_FILENAME = f"stitched_{IIIF_IMAGE_ID}.jpg"

        print(f"Resolved IIIF Image ID: {IIIF_IMAGE_ID}")
        print(f"Resolved Dimensions: {FULL_WIDTH}x{FULL_HEIGHT}")
        
        download_and_stitch_iiif_image(
            IIIF_IMAGE_ID,
            FULL_WIDTH,
            FULL_HEIGHT,
            TILE_SIZE,
            OUTPUT_FILENAME,
            DOWNLOAD_DIR
        )

    except (requests.exceptions.RequestException, ValueError, KeyError) as e:
        print(f"\n--- FATAL ERROR ---")
        print(f"Could not process URL: {e}")
