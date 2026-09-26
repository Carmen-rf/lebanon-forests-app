# Lebanon's Forests: From Carbon Source to Carbon Sink (1990–2021)

**Live app:** https://YOUR-APP-NAME.streamlit.app  <!-- replace after deploying -->

An interactive Streamlit page about how Lebanon's forests went from being a net source of CO2
(when clearing outweighed regrowth, 1990–2010) to a strong net sink (2011–2021).
Built for the Data Visualization & Communication course (MSBA) as an extension of my Plotly assignment.

## What's on the page
- Context on the data and how to read the sign convention (removals are negative, emissions are positive)
- Two headline insights across the full 32-year record
- **Two linked controls:** an *era* radio button (Full record / Loss era / Recovery era) that sets the
  bounds of a *year-range slider*, so users drill down from an era to specific years
- A forest-area line chart (full record in grey for context, with the selected years highlighted) and a
  carbon-flow bar chart (absorbed vs. released vs. net) for the selected years, plus KPI tiles and a
  plain-language summary
- Design justifications for each control, in expanders

## Data
FAO FAOSTAT, *Emissions from Forests*, Lebanon, 1990–2021, via AUB CODEC linked data (`data/Dataset.csv`).

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```
