"""
test_sentinel_pipeline.py

Pruebas unitarias para validar el manejo de parámetros, excepciones y CLI
en sentinel_pipeline.py.
"""

import pytest
from unittest.mock import MagicMock, patch
import numpy as np
import xarray as xr

from sentinel_pipeline import generate_sentinel2_ndvi_composite


def test_empty_stac_search_raises_value_error():
    """Valida que la función lance ValueError si el catálogo STAC no retorna escenas."""
    with patch("pystac_client.Client.open") as mock_stac_client:
        mock_client_instance = MagicMock()
        mock_search = MagicMock()
        mock_item_collection = MagicMock()
        
        # Simula respuesta vacía de STAC
        mock_item_collection.__len__.return_value = 0
        mock_search.item_collection.return_value = mock_item_collection
        mock_client_instance.search.return_value = mock_search
        mock_stac_client.return_value = mock_client_instance

        with pytest.raises(ValueError, match="No se encontraron imágenes"):
            generate_sentinel2_ndvi_composite(
                bbox=[-56.25, -34.90, -56.00, -34.70],
                date_range="2024-01-01/2024-01-02",
                output_path="test_output.nc"
            )


def test_invalid_output_format_raises_value_error():
    """Valida que un formato no soportado (ej. 'jpeg') falle antes de procesar."""
    with patch("pystac_client.Client.open") as mock_stac_client:
        mock_client_instance = MagicMock()
        mock_search = MagicMock()
        mock_item_collection = MagicMock()
        
        # Simula 1 escena encontrada
        mock_item_collection.__len__.return_value = 1
        mock_search.item_collection.return_value = mock_item_collection
        mock_client_instance.search.return_value = mock_search
        mock_stac_client.return_value = mock_client_instance

        # Mock de stackstac para retornar un DataArray ficticio
        with patch("stackstac.stack") as mock_stack:
            dummy_cube = xr.DataArray(
                np.ones((1, 3, 10, 10)),
                dims=["time", "band", "y", "x"],
                coords={
                    "band": ["red", "nir08", "scl"],
                    "time": ["2024-01-01"]
                }
            )
            mock_stack.return_value = dummy_cube

            with pytest.raises(ValueError, match="Formato no soportado"):
                generate_sentinel2_ndvi_composite(
                    bbox=[-56.25, -34.90, -56.00, -34.70],
                    date_range="2024-01-01/2024-01-02",
                    output_path="test_output.jpg",
                    output_format="invalid_format"
                )
