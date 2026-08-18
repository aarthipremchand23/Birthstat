# U.S. Natality Dynamics Dashboard 🏥

Designed for public health officials and healthcare analysts, this interactive **Streamlit** dashboard automatically processes CDC natality data to visualize birth trajectories, state-level volume rankings, and demographic distributions. By providing high-level metrics and intuitive interactive filters, the tool helps decision-makers identify critical seasonal trends to strategically plan for maternity ward capacities and pediatric vaccine schedules.

## 🌟 Key Features

* **Zero-Click Data Ingestion:** Automatically scans the root directory, detects local CSV datasets, and utilizes resilient schema-matching to map column aliases without requiring manual UI uploads.
* **Interactive Visual Analytics:** Features dynamic Plotly charts, including monthly trajectory line charts and stacked horizontal bar charts for state-by-state volume and gender comparisons.
* **Executive KPIs & Filtering:** Includes top-line metrics and robust multiselect filtering (State, Month, Sex) that instantly update the visualizations and the underlying data table.
* **Public Health Signals:** Highlights descriptive, data-driven operational signals to assist with hospital bed allocation and vaccine inventory management.

## 🛠️ Technologies Used

* **Python 3.x**
* **Streamlit:** For building the interactive web application interface.
* **Pandas:** For robust data ingestion, cleaning, and aggregation.
* **Plotly Express:** For generating responsive, interactive visualizations.

## 📂 Project Structure

```text
├── app.py                  # Main Streamlit application script
├── requirements.txt        # Python package dependencies
├── README.md               # Project documentation
└── *.csv                   # Provisional CDC Natality dataset (Drop your file here)
