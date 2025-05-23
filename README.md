# Ohio Parcel Extractor

A command-line tool to extract Ohio parcel data from the Ohio Department of Natural Resources (ODNR) ArcGIS services and export to DXF format for use in CAD software.

## Features

- Extract parcel polygons using state plane coordinates (Ohio North or South)
- Export to DXF format compatible with AutoCAD, BricsCAD, QGIS, etc.
- Support for custom field selection
- Optional parcel labels with PIN and owner information
- Metadata export to JSON format
- Verbose output for debugging

## Installation

1. Clone this repository:
```bash
git clone https://github.com/corykiser/ohio-parcel-extractor.git
cd ohio-parcel-extractor
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
python parcel_extractor.py --bbox 1604764,770138,1609220,765420 --zone south
```

### Advanced Options

```bash
python parcel_extractor.py \
    --bbox 1604764,770138,1609220,765420 \
    --zone south \
    --out my_parcels.dxf \
    --include-labels \
    --export-metadata \
    --verbose
```

### Command Line Options

- `--bbox`: Bounding box coordinates in State Plane format (xmin,ymin,xmax,ymax) **[Required]**
- `--zone`: Ohio State Plane zone (`north` or `south`) [Default: `south`]
- `--out`, `-o`: Output DXF filename [Default: `parcels.dxf`]
- `--fields`: Comma-separated list of fields to fetch [Default: `PIN,OWNER1,OWNER2,ADDRESS,CITY,STATE,ZIP,ACRES`]
- `--include-labels`: Include parcel labels (PIN, owner) in the DXF file
- `--export-metadata`: Export parcel attributes to a separate JSON file
- `--verbose`, `-v`: Enable verbose output
- `--help`, `-h`: Show help message

## Coordinate Systems

This tool uses Ohio State Plane coordinate systems:
- **North Zone**: EPSG:3734 (NAD83 / Ohio North, US Feet)
- **South Zone**: EPSG:3735 (NAD83 / Ohio South, US Feet)

The tool automatically handles coordinate transformation between State Plane and the service's Web Mercator projection.

## Data Source

Data is sourced from the ODNR ArcGIS REST service:
- Service URL: https://gis.ohiodnr.gov/arcgis_site2/rest/services/OIT_Services/odnr_landbase_v2/MapServer
- Parcel Layer: https://gis.ohiodnr.gov/arcgis_site2/rest/services/OIT_Services/odnr_landbase_v2/MapServer/4

## Example Bounding Box

The following bounding box can be used for testing (located in Ohio South zone):
```
1604764,770138,1609220,765420
```

This represents a rectangular area with coordinates:
- Southwest corner: (1604764, 770138)
- Northeast corner: (1609220, 765420)

## Output

### DXF File
The main output is a DXF file containing:
- Parcel boundary polylines on the "PARCELS" layer
- Optional text labels on the "LABELS" layer (when `--include-labels` is used)

### Metadata JSON (Optional)
When `--export-metadata` is used, a JSON file is created containing:
- Total parcel count
- Individual parcel attributes (PIN, owner, address, etc.)

## Converting to DWG

If you need DWG format instead of DXF, you can:
1. Use the free [ODA File Converter](https://www.opendesign.com/guestfiles/oda_file_converter)
2. Open the DXF in your CAD software and save as DWG
3. Use command-line tools like `dxf2dwg` (if available)

## Troubleshooting

### No parcels found
- Verify your bounding box coordinates are in the correct State Plane zone
- Check that coordinates are in feet (not meters)
- Ensure the bounding box covers an area with actual parcels

### Network errors
- Check your internet connection
- The ODNR service may be temporarily unavailable
- Try again with a smaller bounding box

### Invalid coordinates
- Ensure bounding box format is: `xmin,ymin,xmax,ymax`
- Use Ohio State Plane coordinates in US feet
- Verify you're using the correct zone (north vs south)

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
