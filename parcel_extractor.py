#!/usr/bin/env python3
"""
parcel_extractor.py
===================

Fetch Ohio statewide-parcel polygons that fall inside a State-Plane
bounding box (Ohio North or South) and write them to a DXF file.

Example
-------
python parcel_extractor.py \
    --bbox 1604764,770138,1609220,765420 \
    --zone south \
    --out sample_parcels.dxf
"""
import click
import requests
import ezdxf
from pyproj import Transformer
import sys
import json
from pathlib import Path

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
SERVICE_URL = (
    "https://gis.ohiodnr.gov/arcgis_site2/rest/services/"
    "OIT_Services/odnr_landbase_v2/MapServer/4/query"
)

STATE_PLANE = {"north": 3734, "south": 3735}   # EPSG codes (ft-US)
SERVICE_SRID = 3857                            # Web-Mercator (EPSG:3857)

# Default fields to fetch from the service
DEFAULT_FIELDS = "PIN,OWNER1,OWNER2,ADDRESS,CITY,STATE,ZIP,ACRES"

# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def bbox_stateplane_to_service(bbox, zone):
    """
    Re-project a State-Plane bbox (xmin,ymin,xmax,ymax) to the SRID used
    by the ODNR parcel layer (Web-Mercator, EPSG-3857).
    """
    transformer = Transformer.from_crs(
        STATE_PLANE[zone], SERVICE_SRID, always_xy=True
    )
    xmin, ymin, xmax, ymax = bbox
    x0, y0 = transformer.transform(xmin, ymin)
    x1, y1 = transformer.transform(xmax, ymax)
    return min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)


def fetch_parcels(env_service, zone, fields=DEFAULT_FIELDS):
    """
    Query the ArcGIS REST endpoint and return a GeoJSON feature collection.
    """
    xmin, ymin, xmax, ymax = env_service
    params = {
        "f": "geojson",
        "geometryType": "esriGeometryEnvelope",
        "geometry": f"{xmin},{ymin},{xmax},{ymax}",
        "inSR": SERVICE_SRID,
        "outSR": STATE_PLANE[zone],
        "outFields": fields,
        "returnGeometry": "true",
        "where": "1=1",
    }
    
    try:
        r = requests.get(SERVICE_URL, params=params, timeout=60)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.RequestException as e:
        click.echo(f"❌  Error fetching parcels: {e}", err=True)
        raise SystemExit(1)
    except json.JSONDecodeError as e:
        click.echo(f"❌  Error parsing response: {e}", err=True)
        raise SystemExit(1)


def geojson_to_dxf(geojson, dxf_path, include_attributes=False):
    """
    Convert a GeoJSON FeatureCollection (parcel polygons) to a DXF file.
    """
    doc = ezdxf.new(setup=True)
    msp = doc.modelspace()
    
    # Create layers for better organization
    doc.layers.add("PARCELS", color=ezdxf.colors.CYAN)
    if include_attributes:
        doc.layers.add("LABELS", color=ezdxf.colors.YELLOW)

    # Process polygons
    for i, feat in enumerate(geojson["features"]):
        geom = feat["geometry"]
        props = feat.get("properties", {})
        
        # Handle both Polygon and MultiPolygon geometries
        rings_sets = (
            [geom["coordinates"]]  # Polygon → list of rings
            if geom["type"] == "Polygon"
            else geom["coordinates"]  # MultiPolygon → list of list-of-rings
        )

        for rings in rings_sets:
            exterior = rings[0]  # ring[0] = exterior shell
            
            # Add the parcel boundary
            msp.add_lwpolyline(
                exterior, 
                dxfattribs={"closed": True, "layer": "PARCELS"}
            )
            
            # Optionally add labels with parcel information
            if include_attributes and props.get("PIN"):
                # Calculate centroid for label placement
                x_coords = [pt[0] for pt in exterior]
                y_coords = [pt[1] for pt in exterior]
                centroid_x = sum(x_coords) / len(x_coords)
                centroid_y = sum(y_coords) / len(y_coords)
                
                # Create label text
                pin = props.get("PIN", "")
                owner = props.get("OWNER1", "")
                label_text = f"PIN: {pin}\nOwner: {owner}"
                
                msp.add_text(
                    label_text,
                    dxfattribs={
                        "layer": "LABELS",
                        "height": 10,  # Adjust as needed
                        "insert": (centroid_x, centroid_y)
                    }
                )

    doc.saveas(dxf_path)


def export_metadata(geojson, output_path):
    """
    Export parcel metadata to a JSON file for reference.
    """
    metadata = {
        "total_parcels": len(geojson["features"]),
        "parcels": []
    }
    
    for feat in geojson["features"]:
        props = feat.get("properties", {})
        metadata["parcels"].append(props)
    
    with open(output_path, 'w') as f:
        json.dump(metadata, f, indent=2)


# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------
@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.option(
    "--bbox",
    required=True,
    help="Bounding box in State-Plane ft-US: xmin,ymin,xmax,ymax",
)
@click.option(
    "--zone",
    type=click.Choice(["north", "south"], case_sensitive=False),
    default="south",
    show_default=True,
    help="Ohio State-Plane zone of the bbox",
)
@click.option(
    "--out", "-o", 
    default="parcels.dxf", 
    help="Output DXF file"
)
@click.option(
    "--fields",
    default=DEFAULT_FIELDS,
    help="Comma-separated list of fields to fetch from the service"
)
@click.option(
    "--include-labels",
    is_flag=True,
    help="Include parcel labels (PIN, owner) in the DXF file"
)
@click.option(
    "--export-metadata",
    is_flag=True,
    help="Export parcel attributes to a separate JSON file"
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Enable verbose output"
)
def main(bbox, zone, out, fields, include_labels, export_metadata, verbose):
    """Extract Ohio parcel data from ODNR services and export to DXF format.
    
    This tool queries the Ohio Department of Natural Resources (ODNR) ArcGIS
    service for parcel data within a specified bounding box and exports the
    results to a DXF file that can be opened in CAD software.
    
    Example:
        python parcel_extractor.py --bbox 1604764,770138,1609220,765420 --zone south
    """
    # Parse bounding box
    try:
        xmin, ymin, xmax, ymax = map(float, bbox.split(","))
        if len(bbox.split(",")) != 4:
            raise ValueError("Need exactly 4 coordinates")
    except ValueError:
        click.echo("❌  --bbox must be four comma-separated numbers (xmin,ymin,xmax,ymax)", err=True)
        raise SystemExit(1)

    if verbose:
        click.echo(f"📍  Bounding box: {xmin}, {ymin}, {xmax}, {ymax} (State Plane {zone.title()})")
        click.echo(f"📄  Output file: {out}")
        click.echo(f"🏷️   Fields: {fields}")

    # Re-project bounding box to service coordinate system
    click.echo("▶  Re-projecting bounding box to Web Mercator…")
    env_service = bbox_stateplane_to_service((xmin, ymin, xmax, ymax), zone)
    
    if verbose:
        click.echo(f"   Service bbox: {env_service}")

    # Query the service
    click.echo("▶  Querying ODNR parcel service…")
    gj = fetch_parcels(env_service, zone, fields)
    
    if not gj.get("features"):
        click.echo("❌  No parcels found in the specified bounding box")
        raise SystemExit(1)
    
    parcel_count = len(gj["features"])
    click.echo(f"✅  Found {parcel_count} parcels")

    # Build DXF file
    click.echo(f"▶  Building DXF file…")
    geojson_to_dxf(gj, out, include_attributes=include_labels)
    click.echo(f"✅  Saved {out}")
    
    # Export metadata if requested
    if export_metadata:
        metadata_file = Path(out).with_suffix('.json')
        export_metadata(gj, metadata_file)
        click.echo(f"📋  Exported metadata to {metadata_file}")
    
    if verbose:
        click.echo(f"\n📊  Summary:")
        click.echo(f"   • {parcel_count} parcels exported")
        click.echo(f"   • Coordinate system: Ohio State Plane {zone.title()} (EPSG:{STATE_PLANE[zone]})")
        click.echo(f"   • Output file: {out}")
        if include_labels:
            click.echo(f"   • Labels included: Yes")
        if export_metadata:
            click.echo(f"   • Metadata file: {metadata_file}")


if __name__ == "__main__":
    main()
