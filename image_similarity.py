"""
Core logic for finding similar images using perceptual hashing.
Can be used by both GUI and CLI applications.
"""
from pathlib import Path
from PIL import Image
import imagehash
from concurrent.futures import ThreadPoolExecutor, as_completed
import os


class ImageGroup:
    """Represents a group of similar images"""
    def __init__(self, image_paths):
        self.image_paths = image_paths
        self.selected = [False] * len(image_paths)


def _calculate_image_hash(file_path):
    """
    Calculate hashes for a single image.
    Helper function for parallel processing.
    
    Args:
        file_path: Path to the image file
    
    Returns:
        Tuple of (file_path_str, hash_dict) or (file_path_str, None) on error
    """
    try:
        img = Image.open(file_path)
        # Calculate multiple hash types for better accuracy
        hashes = {
            'phash': imagehash.phash(img),      # Perceptual hash (most accurate)
            'dhash': imagehash.dhash(img),      # Difference hash (good for crops)
            'average': imagehash.average_hash(img)  # Average hash (fast)
        }
        return (str(file_path), hashes)
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return (str(file_path), None)


def find_similar_images(folder_path, threshold=5, progress_callback=None):
    """
    Find groups of similar images in a folder.
    
    Args:
        folder_path: Path to the folder containing images
        threshold: Similarity threshold (0-20, lower = more strict)
        progress_callback: Optional callback function(message) for progress updates
    
    Returns:
        List of ImageGroup objects containing similar images
    """
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp'}
    image_hashes = {}  # path -> {hash_type: hash_value}
    
    if progress_callback:
        progress_callback("Scanning images...")
    
    # Collect all image files
    image_files = [
        file_path for file_path in Path(folder_path).rglob('*')
        if file_path.suffix.lower() in image_extensions
    ]
    
    # Calculate hashes for all images in parallel
    max_workers = min(os.cpu_count() or 4, len(image_files))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_path = {executor.submit(_calculate_image_hash, fp): fp for fp in image_files}
        
        # Process completed tasks
        completed = 0
        for future in as_completed(future_to_path):
            path_str, hashes = future.result()
            if hashes is not None:
                image_hashes[path_str] = hashes
            completed += 1
            
            # Update progress periodically
            if progress_callback and completed % 10 == 0:
                progress_callback(f"Processed {completed}/{len(image_files)} images...")
    
    if progress_callback:
        progress_callback(f"Processed {len(image_hashes)} images. Finding similar groups...")
    
    # Find similar images - require at least 2 out of 3 algorithms to agree
    similar_groups = []
    processed = set()
    image_list = list(image_hashes.keys())
    
    for i, path1 in enumerate(image_list):
        if path1 in processed:
            continue
        group = [path1]
        processed.add(path1)
        
        for path2 in image_list[i+1:]:
            if path2 in processed:
                continue
            
            # Check similarity with multiple algorithms
            hash1 = image_hashes[path1]
            hash2 = image_hashes[path2]
            
            matches = 0
            # Perceptual hash is weighted more heavily
            if hash1['phash'] - hash2['phash'] <= threshold:
                matches += 2  # phash counts double
            if hash1['dhash'] - hash2['dhash'] <= threshold:
                matches += 1
            if hash1['average'] - hash2['average'] <= threshold:
                matches += 1
            
            # Require at least 3 points (e.g., phash + one other, or all three)
            if matches >= 3:
                group.append(path2)
                processed.add(path2)
        
        if len(group) > 1:
            similar_groups.append(ImageGroup(group))
    
    return similar_groups
