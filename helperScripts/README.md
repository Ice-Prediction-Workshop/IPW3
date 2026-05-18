## IPW3 Tecplot slicing helper script

This repository provides a Python helper script, `cutTool_ipw3.py`, to extract 2D slices from Tecplot-readable surface data and export them using the IPW3 submission format.

The script is intended to be used after the CFD, droplet, thermodynamic, and geometry post-processing steps have generated surface files. It uses the Tecplot Python API to load the surface solution, extract user-defined spanwise slices, reorder the slice points along the airfoil surface, and write standardized `.dat` files for IPW3 comparisons.

### Tecplot PyTecplot setup

Before running the script, Tecplot must allow external PyTecplot connections.

In Tecplot 360, open:

```text
Scripting -> PyTecplot Connections...
```

Then enable:

```text
Accept connections
```

The default port is usually:

```text
7600
```

Example screenshots:

<img src="figures/helperScript1.png" alt="Opening the PyTecplot Connections menu in Tecplot 360" width="900">

<img src="figures/helperScript2.png" alt="Enabling PyTecplot connections in Tecplot 360" width="900">

### What the script does

The script can extract two main types of IPW3 files:

1. **Cut-data files**

   These contain surface quantities along the requested slice, for example:

   ```text
   X, Y, Z, Cp, HTC, Beta, Ts, FF, k, RhoIce, HTC_CLEAN
   ```

2. **Ice-shape files**

   These contain clean and iced coordinates along the requested slice:

   ```text
   X, Y, Z, X_ICED, Y_ICED, Z_ICED
   ```

The output zone names are automatically formatted using the IPW3 convention, for example:

```text
SLICE_Y_0p9144_BINS03_KS_1mm_CUTDATA
SLICE_Y_0p9144_BINS03_KS_1mm_SINGLE_LAYER_ICE_SHAPE
SLICE_Y_0p9144_BINS03_KS_1mm_FINAL_LAYER_ICE_SHAPE
```

### Main options

| Option | Description |
|---|---|
| `-axis` | Axis direction used to define the slice position. For IPW3 NACA0012 spanwise cuts, this is usually `y`. |
| `-normal` | Normal vector of the slicing plane. For a constant-`y` slice, use `0.0 1.0 0.0`. |
| `-pos` | Slice location or list of slice locations along the selected axis. |
| `-tecplotFiles` | Input Tecplot-readable file, usually a CGNS surface file. |
| `-output` | Output `.dat` file. |
| `--ipw3_CUTDATA` | Write the output using the IPW3 cut-data variable list. |
| `--ipw3_ICE_SHAPE` | Write the output using the IPW3 ice-shape variable list. |
| `--binID` | Droplet-bin identifier used in the zone name, for example `03`, `07`, or `15`. |
| `--OutputType` | Dataset identifier added at the end of the zone name, for example `CUTDATA`, `SINGLE_LAYER_ICE_SHAPE`, or `FINAL_LAYER_ICE_SHAPE`. |
| `--roughnessKS` | Roughness height in mm used in the zone name. For example, `1.0` becomes `KS_1mm`. |

### NACA0012 Example

The following example extracts one IPW3 slice at `Y = 0.9144 m` for a 3-bin result. It writes both the cut-data file and the single-layer ice-shape file.

```bash
# ------------------------------------------------------------------------------
# Tecplot / PyTecplot environment
# ------------------------------------------------------------------------------
# Adjust these paths to match the Tecplot installation on your cluster.
export LD_LIBRARY_PATH=/path/to/tecplot/bin:/path/to/tecplot/bin/sys:${LD_LIBRARY_PATH}
export PATH=/path/to/tecplot/bin:${PATH}
export PYTHONPATH=/path/to/tecplot/python:${PYTHONPATH}

# ------------------------------------------------------------------------------
# User settings
# ------------------------------------------------------------------------------
CUT_TOOL_PATH="./cutTool_ipw3.py"

# Slice location.
SLICE_POSITIONS="0.9144"

# Roughness value written in the IPW3 zone name, in mm.
ROUGHNESS_KS_MM="1.0"

# Droplet-bin identifier.
BIN_ID="03"

# Input files without the .cgns extension.
THERMO_AVG="SOL_THERMO_SURFACE_03_BINS_AVG_KS_1mm"
GEO_AVG="SOL_GEO_SURFACE_03_BINS_AVG_KS_1mm"

# ------------------------------------------------------------------------------
# Extract IPW3 cut-data file
# ------------------------------------------------------------------------------
python "${CUT_TOOL_PATH}" \
  -axis y \
  -normal 0.0 1.0 0.0 \
  -pos ${SLICE_POSITIONS} \
  -tecplotFiles "./${THERMO_AVG}.cgns" \
  -output "./${THERMO_AVG}.dat" \
  --ipw3_CUTDATA \
  --binID "${BIN_ID}" \
  --OutputType CUTDATA \
  --roughnessKS "${ROUGHNESS_KS_MM}"

# ------------------------------------------------------------------------------
# Extract IPW3 ice-shape file
# ------------------------------------------------------------------------------
python "${CUT_TOOL_PATH}" \
  -axis y \
  -normal 0.0 1.0 0.0 \
  -pos ${SLICE_POSITIONS} \
  -tecplotFiles "./${GEO_AVG}.cgns" \
  -output "./${GEO_AVG}.dat" \
  --ipw3_ICE_SHAPE \
  --binID "${BIN_ID}" \
  --OutputType SINGLE_LAYER_ICE_SHAPE \
  --roughnessKS "${ROUGHNESS_KS_MM}"
```

For a final-layer ice shape, replace:

```bash
--OutputType SINGLE_LAYER_ICE_SHAPE
```

with:

```bash
--OutputType FINAL_LAYER_ICE_SHAPE
```

### Example output

For the settings above, the cut-data file will contain a zone name similar to:

```text
ZONE T="SLICE_Y_0p9144_BINS03_KS_1mm_CUTDATA"
```

The ice-shape file will contain a zone name similar to:

```text
ZONE T="SLICE_Y_0p9144_BINS03_KS_1mm_SINGLE_LAYER_ICE_SHAPE"
```

### ONERA M6 example

For the ONERA M6 case, multiple spanwise slices can be extracted in one call. The example below extracts slices at:

```text
Y = 0.1 m, 0.75 m, 1.4 m
```

It writes both the IPW3 cut-data file and the single-layer ice-shape file.

```bash
# ------------------------------------------------------------------------------
# Tecplot / PyTecplot environment
# ------------------------------------------------------------------------------
# Adjust these paths to match the Tecplot installation on your cluster.
export LD_LIBRARY_PATH=/path/to/tecplot/bin:/path/to/tecplot/bin/sys:${LD_LIBRARY_PATH}
export PATH=/path/to/tecplot/bin:${PATH}
export PYTHONPATH=/path/to/tecplot/python:${PYTHONPATH}

# ------------------------------------------------------------------------------
# User settings
# ------------------------------------------------------------------------------
CUT_TOOL_PATH="./cutTool_ipw3.py"

# ONERA M6 IPW3 slice locations.
SLICE_POSITIONS="0.1 0.75 1.4"

# Roughness value written in the IPW3 zone name, in mm.
ROUGHNESS_KS_MM="1.0"

# Droplet-bin identifier.
BIN_ID="03"

# Input files without the .cgns extension.
THERMO_AVG="SOL_THERMO_SURFACE_03_BINS_AVG_KS_1mm"
GEO_AVG="SOL_GEO_SURFACE_03_BINS_AVG_KS_1mm"

# ------------------------------------------------------------------------------
# Extract IPW3 cut-data file
# ------------------------------------------------------------------------------
python "${CUT_TOOL_PATH}" \
  -axis y \
  -normal 0.0 1.0 0.0 \
  -pos ${SLICE_POSITIONS} \
  -tecplotFiles "./${THERMO_AVG}.cgns" \
  -output "./${THERMO_AVG}.dat" \
  --ipw3_CUTDATA \
  --binID "${BIN_ID}" \
  --OutputType CUTDATA \
  --roughnessKS "${ROUGHNESS_KS_MM}"

# ------------------------------------------------------------------------------
# Extract IPW3 ice-shape file
# ------------------------------------------------------------------------------
python "${CUT_TOOL_PATH}" \
  -axis y \
  -normal 0.0 1.0 0.0 \
  -pos ${SLICE_POSITIONS} \
  -tecplotFiles "./${GEO_AVG}.cgns" \
  -output "./${GEO_AVG}.dat" \
  --ipw3_ICE_SHAPE \
  --binID "${BIN_ID}" \
  --OutputType SINGLE_LAYER_ICE_SHAPE \
  --roughnessKS "${ROUGHNESS_KS_MM}"
```

For a final-layer ice shape, replace:

```bash
--OutputType SINGLE_LAYER_ICE_SHAPE
```

with:

```bash
--OutputType FINAL_LAYER_ICE_SHAPE
```

For the settings above, the cut-data file will contain zones similar to:

```text
ZONE T="SLICE_Y_0p1_BINS03_KS_1mm_CUTDATA"
ZONE T="SLICE_Y_0p75_BINS03_KS_1mm_CUTDATA"
ZONE T="SLICE_Y_1p4_BINS03_KS_1mm_CUTDATA"
```

The ice-shape file will contain zones similar to:

```text
ZONE T="SLICE_Y_0p1_BINS03_KS_1mm_SINGLE_LAYER_ICE_SHAPE"
ZONE T="SLICE_Y_0p75_BINS03_KS_1mm_SINGLE_LAYER_ICE_SHAPE"
ZONE T="SLICE_Y_1p4_BINS03_KS_1mm_SINGLE_LAYER_ICE_SHAPE"
```

### Notes

- The script expects Tecplot-readable input files, such as `.cgns`, `.plt`, or `.dat`.
- For CGNS files, the script uses `tecplot.data.load_cgns`.
- For Tecplot files, the script uses `tecplot.data.load_tecplot`.
- The extracted slice is reordered along the surface before writing.
- Missing variables are written as `-999.0` in the IPW3 output.