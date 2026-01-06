10# Similar Images Finder

Find visually similar images in a folder using perceptual hashing.

## Setup

Create venv for deps
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```bash

Install dependencies:
```
pip install -r requirements.txt
```

## Usage

### GUI Version

Launch the graphical interface:
```bash
python find_similar_images_gui.py
```

Or specify a folder and threshold directly:
```bash
python find_similar_images_gui.py <path-to-image-folder> --threshold 10
```

The GUI allows you to:
- Browse and select folders
- Adjust similarity threshold
- Preview similar image groups
- Select images to keep or delete
- Delete selected images with confirmation

### Command Line Version

Basic usage:
```bash
python find_similar_images.py <path-to-image-folder>
```

With custom threshold:
```bash
python find_similar_images.py <path-to-image-folder> --threshold 10
```

### Threshold Guide

- **0**: Identical images
- **1-5**: Very similar (slight variations, crops, or minor edits)
- **6-10**: Similar (noticeable but minor differences)
- **11-20**: Somewhat similar (same subject, different angle/lighting)

Default threshold is **5**.

## Examples

**GUI:**
```bash
python find_similar_images_gui.py ./my_photos --threshold 5
```

**Command Line:**
```bash
# Find very similar images
python find_similar_images.py ./my_photos --threshold 5

# Find images that are somewhat similar
python find_similar_images.py ./my_photos --threshold 15
```

## How It Works

The application uses **multiple perceptual hashing algorithms** for improved accuracy:
1. **Perceptual Hash (pHash)** - Most accurate for detecting similar images
2. **Difference Hash (dHash)** - Good for detecting crops and minor variations
3. **Average Hash** - Fast general-purpose comparison

The process:
1. Resizes images to a small size
2. Converts to grayscale
3. Calculates multiple hash types for each image
4. Compares hashes using Hamming distance
5. Requires agreement from multiple algorithms to group images
6. **Parallel processing** speeds up analysis of large image collections

This multi-algorithm approach is robust to:
- Minor edits and filters
- Slight crops or resizing
- Brightness/contrast adjustments
- JPEG compression artifacts
- Different aspect ratios

## Supported Formats

- JPEG (.jpg, .jpeg)
- PNG (.png)
- BMP (.bmp)
- GIF (.gif)
- TIFF (.tiff)
- WebP (.webp)
## Development

This project was developed with assistance from GitHub Copilot.# Doppio
# Doppio
