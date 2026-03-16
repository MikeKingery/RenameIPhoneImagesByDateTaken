#!/usr/bin/env python3
"""
Media renaming script that processes photos and videos.
Renames files based on the date the photo was taken or video was created.

Supported formats:
- Photos: JPG, HEIC
- Videos: MP4, AVI, MKV, MOV, WMV

Requirements:
    pip install pillow pillow-heif exifread pywin32

Usage:
    python rename_media.py [directory]
    
Examples:
    python rename_media.py                    # Process current directory
    python rename_media.py "C:/Photos"       # Process specific directory
    python rename_media.py ../vacation_pics  # Process relative path
"""

import os
import glob
import sys
import argparse
from datetime import datetime, timedelta
from pathlib import Path
import re
import win32com.client

try:
    from PIL import Image
    from PIL.ExifTags import TAGS
    import pillow_heif
    import exifread
except ImportError as e:
    print(f"Missing required library: {e}")
    print("Please install with: pip install pillow pillow-heif exifread pywin32")
    exit(1)

# Register HEIF opener with Pillow
pillow_heif.register_heif_opener()


def extract_metadata_from_jpg(file_path):
    """Extract date taken and camera model from JPG file using exifread."""
    try:
        with open(file_path, 'rb') as f:
            tags = exifread.process_file(f)
            
        # Get date taken
        date_taken = None
        if 'EXIF DateTimeOriginal' in tags:
            date_taken = str(tags['EXIF DateTimeOriginal'])
        elif 'EXIF DateTime' in tags:
            date_taken = str(tags['EXIF DateTime'])
            
        # Get camera model
        camera_model = ""
        if 'Image Model' in tags:
            camera_model = str(tags['Image Model']).strip()
            
        # Handle GoPro makernote detection if camera model is empty
        if not camera_model and 'EXIF MakerNote' in tags:
            try:
                maker_note = str(tags['EXIF MakerNote'])
                if len(maker_note) > 20:
                    maker_note_substring = maker_note[10:20]
                    if "LAJ8052936" in maker_note_substring:
                        camera_model = "HERO7 Black"
            except:
                pass
                
        return date_taken, camera_model
        
    except Exception as e:
        print(f"Error reading JPG metadata from {file_path}: {e}")
        return None, ""


def extract_metadata_from_heic(file_path):
    """Extract date taken and camera model from HEIC file using Pillow."""
    try:
        with Image.open(file_path) as img:
            exif_data = img.getexif()
            
        # Get date taken (DateTimeOriginal = 36867, DateTime = 306)
        date_taken = None
        if 36867 in exif_data:  # DateTimeOriginal
            date_taken = exif_data[36867]
        elif 306 in exif_data:  # DateTime
            date_taken = exif_data[306]
            
        # Get camera model (Model = 272)
        camera_model = ""
        if 272 in exif_data:
            camera_model = exif_data[272].strip()
            
        return date_taken, camera_model
        
    except Exception as e:
        print(f"Error reading HEIC metadata from {file_path}: {e}")
        return None, ""


def parse_date_string(date_string):
    """Parse date string from EXIF data."""
    if not date_string:
        return None
        
    try:
        # EXIF date format is typically "YYYY:MM:DD HH:MM:SS"
        return datetime.strptime(date_string, "%Y:%m:%d %H:%M:%S")
    except ValueError:
        try:
            # Try alternative format
            return datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            print(f"Could not parse date: {date_string}")
            return None


def extract_video_metadata(file_path):
    """Extract creation date from video file using Shell.Application."""
    try:
        shell = win32com.client.Dispatch("Shell.Application")
        folder_path = os.path.dirname(os.path.abspath(file_path))
        file_name = os.path.basename(file_path)
        
        folder = shell.Namespace(folder_path)
        item = folder.ParseName(file_name)
        
        if not item:
            return None
            
        # Get various date fields and find the oldest one
        dates = []
        
        # Try different metadata fields for video creation date
        date_fields = [
            12,  # Date taken
            208, # Media created  
            3,   # Date modified
            4,   # Date created
        ]
        
        for field_index in date_fields:
            try:
                date_value = folder.GetDetailsOf(item, field_index)
                if date_value and date_value.strip():
                    # Clean Unicode formatting characters
                    clean_date = re.sub(r'[^\d\s/:AMP]', '', date_value)
                    if clean_date.strip():
                        parsed_date = datetime.strptime(clean_date.strip(), "%m/%d/%Y %I:%M %p")
                        dates.append(parsed_date)
            except:
                continue
                
        # Also try file system creation time
        try:
            stat = os.stat(file_path)
            dates.append(datetime.fromtimestamp(stat.st_ctime))
        except:
            pass
            
        # Return the oldest date found
        if dates:
            return min(dates)
            
        return None
        
    except Exception as e:
        print(f"Error reading video metadata from {file_path}: {e}")
        return None


def load_date_adjustments(directory):
    """Load camera date adjustments from rename_media_date_adjustment.txt in the target directory.
    
    File format - one camera model per line, pipe-separated from adjustments:
    
        # This is a comment
        HERO7 Black | years=4 months=8 days=8 hours=-8 minutes=20 seconds=0
        iPhone 13 Pro | hours=-7
        DSC-RX100M7 | hours=5 minutes=30
    
    Only specify the fields you need; omitted fields default to 0.
    Returns a dict keyed by camera model, e.g.:
        { "HERO7 Black": {"years": 4, "months": 8, "days": 8, "hours": -8, "minutes": 20, "seconds": 0} }
    """
    adjustments = {}
    adj_file = os.path.join(directory, "rename_media_date_adjustment.txt")
    
    if not os.path.exists(adj_file):
        return adjustments
    
    with open(adj_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '|' not in line:
                continue
            
            camera_model, _, params = line.partition('|')
            camera_model = camera_model.strip()
            
            fields = {"years": 0, "months": 0, "days": 0, "hours": 0, "minutes": 0, "seconds": 0}
            for token in params.split():
                if '=' in token:
                    key, _, val = token.partition('=')
                    if key.strip() in fields:
                        fields[key.strip()] = int(val.strip())
            
            adjustments[camera_model] = fields
    
    return adjustments


def apply_camera_adjustments(date, camera_model, adjustments):
    """Apply camera-specific date adjustments from the loaded adjustments dict."""
    if not camera_model or camera_model not in adjustments:
        return date
    
    adj = adjustments[camera_model]
    
    # timedelta doesn't support years/months directly, so handle them separately
    try:
        date = date.replace(year=date.year + adj["years"])
        # Add months, rolling over the year if needed
        new_month = date.month + adj["months"]
        date = date.replace(year=date.year + (new_month - 1) // 12, month=(new_month - 1) % 12 + 1)
    except ValueError:
        pass
    
    date = date + timedelta(days=adj["days"], hours=adj["hours"], minutes=adj["minutes"], seconds=adj["seconds"])
    
    return date


def generate_filename(date, file_extension):
    """Generate new filename based on date."""
    # Format: "YYYY-MM-DD HH.MM.SS.ext"
    filename_root = date.strftime("%Y-%m-%d %H.%M.%S")
    return f"{filename_root}.{file_extension}", filename_root


def get_unique_filename(base_filename, filename_root, file_extension):
    """Generate unique filename if file already exists."""
    if not os.path.exists(base_filename):
        return base_filename
        
    # Try appending numbers until we find a unique name
    for i in range(1, 101):
        new_filename = f"{filename_root}-{i}.{file_extension}"
        if not os.path.exists(new_filename):
            return new_filename
            
    # If we can't find a unique name after 100 tries, use the original
    return base_filename


def main():
    """Main function to process photo and video files."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Rename photos and videos based on their creation date",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python rename_media.py                    # Process current directory
  python rename_media.py "C:/Photos"       # Process specific directory
  python rename_media.py ../vacation_pics  # Process relative path
        """
    )
    parser.add_argument(
        'directory', 
        nargs='?', 
        default='.', 
        help='Directory to process (default: current directory)'
    )
    
    args = parser.parse_args()
    
    # Change to target directory
    target_dir = os.path.abspath(args.directory)
    if not os.path.exists(target_dir):
        print(f"Error: Directory '{target_dir}' does not exist.")
        return
    
    if not os.path.isdir(target_dir):
        print(f"Error: '{target_dir}' is not a directory.")
        return
    
    # Store original directory and change to target
    original_dir = os.getcwd()
    os.chdir(target_dir)
    
    print(f"Processing files in: {target_dir}")
    
    try:
        # Load date adjustments once before the loop
        adjustments = load_date_adjustments(target_dir)
        if adjustments:
            print(f"Loaded date adjustments for: {', '.join(adjustments.keys())}")
        # Get all supported files in target directory
        photo_extensions = ["*.jpg", "*.JPG", "*.heic", "*.HEIC"]
        video_extensions = ["*.mp4", "*.MP4", "*.avi", "*.AVI", "*.mkv", "*.MKV", 
                           "*.mov", "*.MOV", "*.wmv", "*.WMV"]
        
        photo_files = []
        video_files = []
        
        for pattern in photo_extensions:
            photo_files.extend(glob.glob(pattern))
        
        for pattern in video_extensions:
            video_files.extend(glob.glob(pattern))
        
        all_files = photo_files + video_files
        
        if not all_files:
            print("No supported photo or video files found in directory.")
            print("Supported formats: JPG, HEIC, MP4, AVI, MKV, MOV, WMV")
            return
            
        print(f"Found {len(all_files)} files to process ({len(photo_files)} photos, {len(video_files)} videos)...")
        
        # Process files one by one, checking if they still exist
        for file_path in all_files:
            if not os.path.exists(file_path):
                continue  # Skip if file was already renamed or doesn't exist
            try:
                # Get file extension
                file_extension = Path(file_path).suffix.lower().lstrip('.')
                
                # Extract metadata based on file type
                date = None
                camera_model = ""
                
                if file_extension == 'jpg':
                    date_taken_string, camera_model = extract_metadata_from_jpg(file_path)
                    if date_taken_string:
                        date = parse_date_string(date_taken_string)
                elif file_extension == 'heic':
                    date_taken_string, camera_model = extract_metadata_from_heic(file_path)
                    if date_taken_string:
                        date = parse_date_string(date_taken_string)
                elif file_extension in ['mp4', 'avi', 'mkv', 'mov', 'wmv']:
                    # For videos, extract creation date
                    date = extract_video_metadata(file_path)
                    # Camera model detection for videos is limited, but we can try
                    # Most video metadata doesn't include camera model reliably
                    
                if not date:
                    print(f"Could not extract date from {file_path}")
                    continue
                    
                # Apply camera-specific adjustments
                adjusted_date = apply_camera_adjustments(date, camera_model, adjustments)
                
                # Generate new filename
                new_filename, filename_root = generate_filename(adjusted_date, file_extension)
                
                # Check if rename is needed
                if file_path == new_filename:
                    print(f"{file_path} == Not renaming")
                    continue
                    
                # Get unique filename if needed
                final_filename = get_unique_filename(new_filename, filename_root, file_extension)
                
                # Perform the rename
                os.rename(file_path, final_filename)
                print(f"{file_path} -> {final_filename}")
                
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
    
    finally:
        # Always return to original directory
        os.chdir(original_dir)


if __name__ == "__main__":
    main()