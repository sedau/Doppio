"""
Command-line application to find similar images.
"""
import argparse
import os
from pathlib import Path
from image_similarity import find_similar_images


def format_size(size_bytes):
    """Format file size in human-readable format"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def main():
    parser = argparse.ArgumentParser(
        description='Find similar images in a folder using perceptual hashing'
    )
    parser.add_argument('folder', help='Path to folder containing images')
    parser.add_argument('--threshold', type=int, default=5,
                       help='Similarity threshold (0-20, lower = more strict, default=5)')
    parser.add_argument('--output', '-o', help='Output file to save results (optional)')
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.folder):
        print(f"Error: '{args.folder}' is not a valid directory")
        return 1
    
    print(f"Scanning folder: {args.folder}")
    print(f"Threshold: {args.threshold}")
    print("-" * 80)
    
    # Find similar images
    groups = find_similar_images(
        args.folder,
        threshold=args.threshold,
        progress_callback=lambda msg: print(msg)
    )
    
    if not groups:
        print("\nNo similar images found. Try increasing the threshold.")
        return 0
    
    print(f"\nFound {len(groups)} groups of similar images:\n")
    
    output_lines = []
    
    # Display results
    for idx, group in enumerate(groups, 1):
        print(f"Group {idx} ({len(group.image_paths)} images):")
        output_lines.append(f"Group {idx} ({len(group.image_paths)} images):")
        
        for img_path in group.image_paths:
            path = Path(img_path)
            size = os.path.getsize(img_path)
            size_str = format_size(size)
            
            line = f"  - {path.name} ({size_str}) - {img_path}"
            print(line)
            output_lines.append(line)
        
        print()
        output_lines.append("")
    
    # Save to file if requested
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write('\n'.join(output_lines))
        print(f"Results saved to: {args.output}")
    
    print(f"Total: {len(groups)} groups found")
    return 0


if __name__ == '__main__':
    exit(main())
