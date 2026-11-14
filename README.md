# 🛰️ First Rain from Orbit: NISAR L-Band Soil Moisture & Salt-Lake Dynamics in Konya Basin

**2026 NASA International Space Apps Challenge** · **Challenge:** *Dancing with the SARs*  
**Team:** TAU IEEE CS (Turkish-German University, Istanbul, Türkiye)  
**License:** [Apache License 2.0](https://www.opensource.org/licenses/Apache-2.0)

---

## 1. Overview & Scientific Story

Can we watch autumn's first rain quench a drought-stricken agricultural plain from space—even through clouds?

Between **September 6, 2026 (Dry Baseline)** and **September 18, 2026 (Post-Rain)**, Team **TAU IEEE CS** analyzed real co-registered **NASA-ISRO SAR (NISAR) Level-2 GCOV (`HHHH`, $\lambda = 24.4\text{ cm}$)**, **Level-2 GUNW**, and **Level-3 SME2** radar datasets over Türkiye's largest closed agricultural basin: the **Konya Plain and Lake Tuz** (`38.4°N, 33.3°E`, UTM Zone 36N `EPSG:32636`).

Our analysis revealed two opposite microwave physics mechanisms triggered by the same rainfall event:
1. **Agricultural Plain Brightening (`+2.40 dB` scene median):** Rainwater entering the top 5 cm of dry soil raised its relative dielectric permittivity ($\varepsilon_r$ jumping from $\sim 4$ to $\sim 15\text{–}25$), boosting L-band HH surface backscatter by ~74% in linear power.
2. **Lake Tuz Specular Darkening (`-0.62 dB` median, down to `-4.0 dB` in central brine pools):** Rainwater forming a thin, smooth film over the flat crystalline salt pan acted as a specular mirror, reflecting radar pulses away from the satellite antenna.

---

## 2. Three-Pillar Independent Physical Validation

| Validation Pillar | Dataset / Method | Measured Result | Physical Interpretation |
| :--- | :--- | :--- | :--- |
| **1. Urban Corner-Reflector Control** | NISAR L2 `GCOV` (`HHHH`, 2 km radius) | **Konya:** `+0.30 dB`<br>**Aksaray:** `+0.49 dB`<br>**Kulu:** `+1.94 dB`<br>**Scene Median:** `+2.40 dB` | Dense urban concrete/asphalt double-bounce targets stayed near `0 dB`, proving the `+2.40 dB` farmland shift is real surface wetting, not sensor calibration drift. |
| **2. Precipitation Record** | [NASA POWER API](https://power.larc.nasa.gov/) (`PRECTOTCORR`) | **6–15 Sep:** `0.0 mm`<br>**16–17 Sep:** `5.9 mm`<br>**18 Sep:** `~8.1 mm/day` | Ten consecutive dry days followed by autumn's first rainfall right before the Sep 18 (`02:53:33 UTC` / `05:53 TRT`) NISAR pass. |
| **3. L3 Soil Moisture Product** | NISAR L3 `SME2` (`Track 172 A`) | **6 Sep:** `0.162 m³/m³`<br>**18 Sep:** `0.220 m³/m³` (**`+35.8%`**) | Independent Level-3 soil moisture retrieval confirms a `+0.058 m³/m³` volumetric soil moisture jump across the basin. |

---

## 3. Repository Structure

* `nisar_konya_spaceapps.ipynb` — End-to-end Google Colab notebook that queries [NASA ASF DAAC](https://search.asf.alaska.edu/) via `asf_search`, processes HDF5 granules (`GCOV`, `GUNW`, `SME2`), runs the $5\times5$ speckle filter and $\pm 3.0\text{ dB}$ change detector, and exports all figures and `numbers.json`.
* `index.html` — Self-contained interactive web observatory (Before/After curtain slider, $\Delta\text{dB}$ log-ratio viewer, and 3-pillar validation dashboard).
* `NISAR_Konya_7Slides_Presentation.pdf` — 7-slide project demonstration presentation deck.
* `gcov_fark.png` & `panel_2x2.png` — NISAR L2 GCOV HH Before (6 Sep), After (18 Sep), Log-Ratio Difference, and $\pm 3.0\text{ dB}$ Change Map.
* `sme2_nem.png` & `yagis.png` — NISAR L3 SME2 soil moisture and NASA POWER daily precipitation validation plots.
* `gunw_hareket.png` — NISAR L2 GUNW L-band unwrapped phase map ($\lambda = 24.4\text{ cm}$), illustrating tropospheric wet delay and moisture phase effects across the 12-day interval.
* `numbers.json` — Exported quantitative telemetry and bounding-box metadata.

---

## 4. How to Run in Google Colab (15 Minutes)

1. Create a free account at [NASA Earthdata Login](https://urs.earthdata.nasa.gov/).
2. Open `nisar_konya_spaceapps.ipynb` in [Google Colab](https://colab.research.google.com/).
3. Replace `KULLANICI = "eralp52"` in Cell 2 with your Earthdata username and run all cells top-to-bottom.

---

## 5. Data & Open-Source Software Citations

* **NASA Data:**
  * NASA-ISRO SAR (NISAR) Level-2 GCOV (`NISAR_L2_PR_GCOV`) & Level-2 GUNW (`NISAR_L2_PR_GUNW`), Track 172 Ascending, accessed via [NASA ASF DAAC](https://search.asf.alaska.edu/).
  * NASA-ISRO SAR (NISAR) Level-3 Soil Moisture (`NISAR_L3_PR_SME2_029/030_172_A`), accessed via [NASA ASF DAAC](https://asf.alaska.edu/datasets/daac/nisar/).
  * NASA Prediction Of Worldwide Energy Resources ([NASA POWER Agroclimatology API](https://power.larc.nasa.gov/)).
  * [NASA Earthdata Login](https://urs.earthdata.nasa.gov/).
* **Partner & Calibration Reference:**
  * [ISRO NISAR Mission](https://www.isro.gov.in/NISAR.html) & [CEOS Cal/Val Portal — Tuz Gölü Landnet Site](https://calvalportal.ceos.org/).
* **Open-Source Software & Libraries:**
  * [`asf_search`](https://github.com/asfadmin/Discovery-asf_search) (BSD-3-Clause), [`h5py`](https://www.h5py.org/) (BSD-3-Clause), [`NumPy`](https://numpy.org/) (BSD-3-Clause), [`SciPy`](https://scipy.org/) (BSD-3-Clause), [`Matplotlib`](https://matplotlib.org/) (PSF License), [`pyproj`](https://pyproj4.github.io/pyproj/) (MIT License), [`Tailwind CSS`](https://tailwindcss.com/) (MIT License).

---

## 6. Mandatory Super Intelligence (SI) / AI Disclosure

In compliance with 2026 NASA Space Apps Challenge rules, Team **TAU IEEE CS** declares that generative AI tools—**Claude (Anthropic)** and **Gemini (Google)**—were used as coding, debugging, and layout assistants for structuring the Python HDF5 visualization script, styling the HTML/CSS web interface, and formatting English documentation. All scientific hypotheses, NISAR data selections, Colab executions, and physical validations were performed and verified by the human team on real NASA observational data. No AI-generated imagery is presented as satellite data.
