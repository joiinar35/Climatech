"""
sentinel_pipeline.py

Módulo e interfaz de línea de comandos (CLI) para procesamiento Sentinel-2.
Extrae compuestos NDVI con filtrado SCL vía STAC y exporta a NetCDF o GeoTIFF.
"""

import argparse
import logging
from typing import List, Sequence, Literal
import pystac_client
import stackstac
import xarray as xr
import rioxarray

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def generate_sentinel2_ndvi_composite(
    bbox: Sequence[float],
    date_range: str,
    output_path: str,
    max_scene_cloud_cover: float = 30.0,
    valid_scl_classes: List[int] = [4, 5, 6, 7],
    epsg: int = 32721,
    resolution: float = 10.0,
    output_format: Literal["netcdf", "geotiff"] = "netcdf",
    stac_url: str = "https://earth-search.aws.element84.com/v1"
) -> xr.DataArray:
    """
    Consulta imágenes Sentinel-2 L2A desde un catálogo STAC, aplica enmascaramiento
    de nubes a nivel de píxel (SCL), genera el compuesto NDVI y exporta a disco.
    """
    logger.info("Conectando al catálogo STAC: %s", stac_url)
    client = pystac_client.Client.open(stac_url)

    logger.info("Buscando escenas Sentinel-2 L2A (%s) para BBOX %s...", date_range, bbox)
    search = client.search(
        collections=["sentinel-2-c1-l2a"],
        bbox=bbox,
        datetime=date_range,
        query={"eo:cloud_cover": {"lt": max_scene_cloud_cover}}
    )

    items = search.item_collection()
    num_items = len(items)
    logger.info("Se encontraron %d escenas.", num_items)

    if num_items == 0:
        raise ValueError("No se encontraron imágenes en el catálogo STAC con los parámetros indicados.")

    logger.info("Construyendo cubo multidimensional perezoso con stackstac...")
    cube = stackstac.stack(
        items,
        assets=["red", "nir08", "scl"],
        bounds_latlon=bbox,
        epsg=epsg,
        resolution=resolution
    )

    logger.info("Enmascarando nubes y sombras con capa SCL...")
    scl = cube.sel(band="scl")
    valid_mask = scl.isin(valid_scl_classes)

    red = cube.sel(band="red").where(valid_mask)
    nir = cube.sel(band="nir08").where(valid_mask)

    logger.info("Calculando índice NDVI y compuesto temporal...")
    ndvi = (nir - red) / (nir + red)
    composite = ndvi.mean(dim="time", skipna=True)

    logger.info("Ejecutando cómputo en memoria...")
    resultado_computed = composite.compute()

    if output_format == "netcdf":
        logger.info("Exportando a NetCDF: %s", output_path)
        resultado_computed.name = "ndvi_composite"
        resultado_computed.attrs["description"] = "Compuesto temporal de NDVI filtrado por nubes"
        resultado_computed.attrs["sensor"] = "Sentinel-2 L2A"
        encoding = {"ndvi_composite": {"zlib": True, "complevel": 5, "dtype": "float32", "_FillValue": -9999.0}}
        resultado_computed.to_netcdf(output_path, encoding=encoding)

    elif output_format == "geotiff":
        logger.info("Exportando a GeoTIFF: %s", output_path)
        resultado_computed = resultado_computed.rio.write_crs(f"EPSG:{epsg}")
        resultado_computed = resultado_computed.rio.write_nodata(-9999.0)
        resultado_computed.rio.to_raster(
            output_path,
            driver="GTiff",
            dtype="float32",
            compress="LZW",
            tiled=True,
            blockxsize=256,
            blockysize=256
        )

    logger.info("Proceso completado con éxito.")
    return resultado_computed


def main():
    parser = argparse.ArgumentParser(
        description="CLI para generación de compuestos NDVI Sentinel-2 vía STAC."
    )
    parser.add_argument(
        "--bbox",
        nargs=4,
        type=float,
        required=True,
        metavar=("MIN_LON", "MIN_LAT", "MAX_LON", "MAX_LAT"),
        help="Coordenadas de la región: min_lon min_lat max_lon max_lat"
    )
    parser.add_argument(
        "--dates",
        type=str,
        required=True,
        help="Rango de fechas en formato 'AAAA-MM-DD/AAAA-MM-DD'"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        required=True,
        help="Ruta del archivo de salida (.nc o .tif)"
    )
    parser.add_argument(
        "--cloud-cover",
        type=float,
        default=30.0,
        help="Porcentaje máximo de nubes por escena (default: 30.0)"
    )
    parser.add_argument(
        "--epsg",
        type=int,
        default=32721,
        help="Código EPSG para proyección objetivo (default: 32721)"
    )
    parser.add_argument(
        "--resolution",
        type=float,
        default=10.0,
        help="Resolución espacial en metros (default: 10.0)"
    )
    parser.add_argument(
        "--format",
        choices=["netcdf", "geotiff"],
        default="netcdf",
        help="Formato de salida: netcdf o geotiff (default: netcdf)"
    )

    args = parser.parse_args()

    try:
        generate_sentinel2_ndvi_composite(
            bbox=args.bbox,
            date_range=args.dates,
            output_path=args.output,
            max_scene_cloud_cover=args.cloud_cover,
            epsg=args.epsg,
            resolution=args.resolution,
            output_format=args.format
        )
    except Exception as e:
        logger.error("Error durante la ejecución: %s", e)
        exit(1)


if __name__ == "__main__":
    main()
