import os
from io import BytesIO
from osm_fieldwork.basemapper import create_basemap_file


def main():
    boundary = f"{os.path.dirname(os.path.abspath(__file__))}/../tests/testdata/Rollinsville.geojson"
    with open(boundary, "rb") as geojson_file:
        boundary = geojson_file.read()  # read as a `bytes` object.
        boundary_bytesio = BytesIO( boundary)  # add to a BytesIO wrapper

    create_basemap_file(
        verbose=True,
        boundary=boundary_bytesio,
        outfile="outreachy.mbtiles",
        zooms="12-15",
        source="esri",
    )


if __name__ == "__main__":
    main()
