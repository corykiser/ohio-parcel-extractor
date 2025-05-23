#!/usr/bin/env python3
"""
test_extraction.py
==================

Test script to verify the parcel extractor works correctly with the example bounding box.

Usage:
    python test_extraction.py
"""

import subprocess
import sys
from pathlib import Path

def run_test():
    """Run the parcel extractor with test parameters."""
    
    # Test parameters from the original example
    bbox = "1604764,770138,1609220,765420"
    zone = "south"
    output_file = "test_parcels.dxf"
    
    print("🧪 Running Ohio Parcel Extractor test...")
    print(f"   Bounding box: {bbox}")
    print(f"   Zone: {zone}")
    print(f"   Output: {output_file}")
    print()
    
    # Build command
    cmd = [
        sys.executable, 
        "parcel_extractor.py",
        "--bbox", bbox,
        "--zone", zone,
        "--out", output_file,
        "--include-labels",
        "--export-metadata",
        "--verbose"
    ]
    
    try:
        # Run the command
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        print("✅ Command executed successfully!")
        print("\nOutput:")
        print(result.stdout)
        
        # Check if files were created
        dxf_path = Path(output_file)
        json_path = Path(output_file).with_suffix('.json')
        
        if dxf_path.exists():
            print(f"✅ DXF file created: {dxf_path} ({dxf_path.stat().st_size} bytes)")
        else:
            print(f"❌ DXF file not found: {dxf_path}")
            
        if json_path.exists():
            print(f"✅ Metadata file created: {json_path} ({json_path.stat().st_size} bytes)")
        else:
            print(f"❌ Metadata file not found: {json_path}")
            
        return True
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed with return code {e.returncode}")
        print("\nStdout:")
        print(e.stdout)
        print("\nStderr:")
        print(e.stderr)
        return False
    except FileNotFoundError:
        print("❌ Could not find parcel_extractor.py")
        print("   Make sure you're running this from the repository root directory")
        return False

if __name__ == "__main__":
    success = run_test()
    
    if success:
        print("\n🎉 Test completed successfully!")
        print("\nNext steps:")
        print("1. Open test_parcels.dxf in your CAD software")
        print("2. Verify the parcels are displayed correctly")
        print("3. Check test_parcels.json for parcel metadata")
    else:
        print("\n💥 Test failed. Please check the error messages above.")
    
    sys.exit(0 if success else 1)
