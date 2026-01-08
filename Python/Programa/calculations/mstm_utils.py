import numpy as np
import sys
import os
import requests
import yaml


def compute_parameters(radius, wavelength, n_real=None, n_imag=None, material=None):
    """
    Compute dimensionless MSTM parameters.
    
    Parameters
    ----------
    radius : float
        Sphere radius in the same units as wavelength (e.g., nm or µm).
    wavelength : float
        Wavelength in the same units as radius.
    n_real : float, optional
        Real part of refractive index.
    n_imag : float, optional
        Imaginary part of refractive index.
    material : str, optional
        If given (e.g. "Au"), fetch refractive index data from the web.
    
    Returns
    -------
    dict
        Dictionary with length_scale_factor, size_parameter, and refractive_index.
    """
    if wavelength <= 0:
        raise ValueError("Wavelength must be positive.")
    if radius <= 0:
        raise ValueError("Radius must be positive.")

    # MSTM scaling
    length_scale_factor = 2 * np.pi / wavelength
    size_parameter = length_scale_factor * radius

    results = {
        "radius_input": radius,
        "wavelength_input": wavelength,
        "length_scale_factor": length_scale_factor,
        "size_parameter": size_parameter,
    }
    print("material:", material)

    # Handle refractive index
    if material is not None and material.lower() in ["au","ag", "al", "cu", "fe", "h2o"]:
        
        # Fetch refractive index data from refractiveindex.info
        # webLink = {
        #     "au": "https://refractiveindex.info/tmp/database/data-nk/main/Au/Johnson.txt",
        #     "ag": "https://refractiveindex.info/tmp/database/data-nk/main/Ag/Johnson.txt",
        #     "al": "https://refractiveindex.info/tmp/database/data-nk/main/Al/Rakic.txt",
        #     "cu": "https://refractiveindex.info/tmp/database/data-nk/main/Cu/Johnson.txt",
        #     "fe": "https://refractiveindex.info/tmp/database/data-nk/main/Fe/Johnson.txt",
        # }

        data_dir ={
            "au": "./Python/Programa/calculations/data/au_johnson.txt",
            "ag": "./Python/Programa/calculations/data/ag_johnson.txt",
            "al": "./Python/Programa/calculations/data/al_rakic.txt",
            "cu": "./Python/Programa/calculations/data/cu_johnson.txt",
            "fe": "./Python/Programa/calculations/data/fe_johnson.txt",
            "h2o": "./Python/Programa/calculations/data/h2o_hale_querry.txt",
        }

        data_file = data_dir.get(material.lower())
        print("Using data file:", data_file)
        if data_file is None:
            raise ValueError(f"Unknown material: {material}")

        data = np.genfromtxt(
            data_file,
            delimiter="\t"
        )
    
        N = len(data) // 2
        waveLength = data[1:N, 0]
        realRefractiveInd = data[1:N, 1]
        imRefractiveInd = data[N+1:, 1]  # convention: imaginary part positive in mstm
        # imRefractiveInd = -data[N+1:, 1]  # convention: imaginary part negative in miepython
        refractiveIndex = realRefractiveInd + 1.0j * imRefractiveInd


        # Interpolate at requested wavelength
        n_real_interp = np.interp(wavelength, waveLength, realRefractiveInd)
        n_imag_interp = np.interp(wavelength, waveLength, imRefractiveInd)
        results["refractive_index"] = complex(n_real_interp, n_imag_interp)
        
    elif n_real is not None:
        if n_imag is None:
            n_imag = 0.0
        results["refractive_index"] = complex(n_real, n_imag)

    return results


if __name__ == "__main__":
    if len(sys.argv) == 3:
        r = float(sys.argv[1])
        wl = float(sys.argv[2])
        results = compute_parameters(r, wl)
        print(results)
    elif len(sys.argv) == 5:
        r = float(sys.argv[1])
        wl = float(sys.argv[2])
        n_real = float(sys.argv[3])
        n_imag = float(sys.argv[4])
        results = compute_parameters(r, wl, n_real, n_imag)
        print(results)
    elif len(sys.argv) == 4 and sys.argv[3].lower() == "au":
        r = float(sys.argv[1])
        wl = float(sys.argv[2])
        results = compute_parameters(r, wl, material="Au")
        print(results)
    else:
        print("Usage:")
        print("  python mstm_utils.py <radius> <wavelength>")
        print("  python mstm_utils.py <radius> <wavelength> <n_real> <n_imag>")
        print("  python mstm_utils.py <radius> <wavelength> Au")
