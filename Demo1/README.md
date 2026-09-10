# Cloud-Native Sentinel-2 NDVI Pipeline

[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

An end-to-end, cloud-native geospatial Python pipeline for automated query, processing, cloud masking, and temporal aggregation of **Sentinel-2 L2A** satellite imagery using **STAC APIs**, **`Xarray`**, **`stackstac`**, and **`Dask`**.

---

## 📌 Overview

This repository provides an enterprise-ready pipeline designed to process petabyte-scale Earth Observation (EO) data directly in the cloud without downloading full satellite scenes. 

By leveraging **Cloud-Optimized GeoTIFFs (COGs)** and **STAC (SpatioTemporal Asset Catalog)** endpoints, the pipeline streams only the pixels required within a specific Bounding Box (BBOX) and temporal window.

### Key Features

- **Cloud-Native Data Streaming:** Queries Element 84's STAC API (AWS Open Data) using `pystac-client` and streams pixel subsets via HTTP Range Requests using `stackstac`.
- **Pixel-Level Cloud Masking:** Employs Sentinel-2 Scene Classification Layer (SCL) to mask out clouds, cirrus, and cloud shadows before calculations.
- **Out-of-Core Processing:** Utilizes `Dask` lazy evaluation to manage memory efficiently when performing temporal aggregations.
- **Spectral Index Computation:** Calculates Normalized Difference Vegetation Index (NDVI) across multidimensional data cubes.
- **Flexible Export Formats:** Supports export to metadata-rich **NetCDF4** (`.nc`) or compressed **GeoTIFF** (`.tif`).
- **Dual Interface:** Fully usable as both a Python module (`import`) and a command-line tool (CLI).

---

## 🛠️ Architecture & Data Flow
+-------------------+      +-----------------------+      +-----------------------+
|  STAC Catalog     | ---> |  stackstac DataCube   | ---> |  SCL Cloud Masking    |
| (Element 84 AWS)  |      | (Lazy / Dask Array)   |      | (Pixel Filtering)     |
+-------------------+      +-----------------------+      +-----------------------+
|
v
+-------------------+      +-----------------------+      +-----------------------+
| Export Output     | <--- |  Temporal Aggregation | <--- |  NDVI Calculation     |
| (NetCDF / GeoTIFF)|      | (Mean across Time)    |      | (NIR - RED)/(NIR+RED) |
+-------------------+      +-----------------------+      +-----------------------+

## ⚙️ Installation

### Prerequisites

- Python 3.10+
- `conda` or `mamba` (recommended for geospatial C-libraries)

### Setup Environment

```bash
# Clone repository
git clone [https://github.com/your-username/sentinel2-cloud-native-pipeline.git](https://github.com/your-username/sentinel2-cloud-native-pipeline.git)
cd sentinel2-cloud-native-pipeline

# Create isolated environment using Conda
conda create -n geo_env python=3.11 -y
conda activate geo_env

# Install dependencies from conda-forge
conda install -c conda-forge pystac-client stackstac xarray rasterio rioxarray dask netcdf4 -y
```

Argument,Description,Default
--bbox,Spatial bounding box: min_lon min_lat max_lon max_lat,Required
--dates,Temporal range: 'YYYY-MM-DD/YYYY-MM-DD',Required
"-o, --output",Output file path (.nc or .tif),Required
--cloud-cover,Maximum scene-level cloud coverage threshold (%),30.0
--epsg,Target CRS EPSG projection code,32721 (UTM 21S)
--resolution,Spatial resolution in meters,10.0
--format,Output format (netcdf or geotiff),netcdf

