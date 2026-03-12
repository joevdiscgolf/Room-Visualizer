# Room Layout Visualizer

Interactive room layout planner for headboard strips and lighting placement.

## Features

- Adjust room dimensions with interactive sliders
- Configure bed, nightstands, and headboard strips
- Three layout modes for strip placement
- Real-time visualization
- All measurements in inches

## Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Opens at http://localhost:8501

## Deploy to Streamlit Cloud

1. Push this repo to GitHub
2. Go to https://share.streamlit.io/
3. Click "New app"
4. Select this repository
5. Main file: `app.py`
6. Click "Deploy"

## Usage

Use the sliders in the left sidebar to:
- Set room width
- Adjust nightstand and bed dimensions
- Configure headboard strip count and width
- Position lights
- Choose layout mode (even gaps, start left, or start right)

The visualization updates in real-time as you adjust the settings.
