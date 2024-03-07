from io import BytesIO
from osm_fieldwork.basemapper import create_basemap_file


def main():
    with open("/Users/valentinabuoro/outreachy/osm-fieldwork/tests/testdata/Rollinsville.geojson", "rb") as geojson_file:
        boundary = geojson_file.read()  # read as a `bytes` object.
        boundary_bytesio = BytesIO( boundary)  # add to a BytesIO wrapper

    create_basemap_file(
        verbose=True,
        boundary=boundary_bytesio,
        outfile=None,
        zooms="12-15",
        source="esri",
    )


if __name__ == "__main__":
    """This is just a hook so this file can be run standlone during development."""
    main()
