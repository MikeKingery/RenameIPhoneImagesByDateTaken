# Media Renaming Script

This repository contains a Python script to rename photo and video files based on the date they were taken or created.

## Main Script

### Python Version (`rename_media.py`)
- **Platform**: Cross-platform (Windows, macOS, Linux)
- **Requirements**: Python 3.6+ with required packages
- **Method**: Uses pillow-heif for HEIC, exifread for JPG, and Shell.Application for video metadata extraction
- **Supports**: Photos (JPG, HEIC) and Videos (MP4, AVI, MKV, MOV, WMV)

## Legacy PowerShell Scripts

The original PowerShell scripts have been moved to the `_backups` folder:
- `RenameIPhotos.ps1` - Photo renaming (JPG, HEIC)
- `RenameVideos.ps1` - Video renaming (MP4, AVI, MKV, MOV, WMV)

## Installation

```bash
# Install required packages
pip install -r requirements.txt

# Or install individually
pip install pillow pillow-heif exifread pywin32

# Run the script
python rename_media.py
```

## Features

- **Multi-Format Support**: Processes photos (JPG, HEIC) and videos (MP4, AVI, MKV, MOV, WMV)
- **Date Extraction**: Extracts "Date Taken" from EXIF metadata for photos, creation date for videos
- **Camera Detection**: Identifies camera model for specific adjustments
- **Date Adjustments**: Applies camera-specific date corrections (configurable)
- **Duplicate Handling**: Automatically appends numbers for duplicate filenames
- **Safe Renaming**: Only renames files when the filename would actually change
- **Smart Video Dating**: Uses oldest available date from multiple metadata fields for videos

## Filename Format

Files are renamed to: `YYYY-MM-DD HH.MM.SS.ext`

Example: `2025-10-15 08.22.22.heic`

## Camera-Specific Adjustments

The scripts include logic for camera-specific date adjustments:

- **iPhone 13 Pro / iPhone 15 Pro**: Currently no adjustment (commented out)
- **GoPro HERO7 Black**: Adds 4 years, 8 months, 8 days, subtracts 8 hours, adds 20 minutes
- **Other cameras**: Currently no adjustment (commented out)

These adjustments can be modified in the source code as needed.

## Usage

1. Place the script in the directory containing your photos and videos
2. Run the script: `python rename_media.py`
3. Files will be renamed based on their metadata (EXIF date for photos, creation date for videos)

## Supported File Types

### Photos
- **JPG/JPEG**: Full support including GoPro makernote detection
- **HEIC**: Full support for Apple's HEIC format

### Videos
- **MP4**: MPEG-4 video files
- **AVI**: Audio Video Interleave files
- **MKV**: Matroska video files
- **MOV**: QuickTime movie files
- **WMV**: Windows Media Video files

## Error Handling

- Files without readable metadata are skipped with a warning
- Duplicate filenames are handled by appending incremental numbers
- Processing continues even if individual files fail

## Notes

- Cross-platform compatibility (Windows, macOS, Linux)
- Preserves original file extensions
- Processes files in the current working directory only
- Legacy PowerShell scripts available in `_backups` folder for reference