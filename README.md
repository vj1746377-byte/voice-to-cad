# Voice-to-CAD Prompt Assistant

A web app that converts plain-English design requests into ready-to-run FreeCAD Python scripts, using Google's Gemini AI.

## Problem

Designing parametric CAD models usually requires knowing a CAD tool's scripting API. Voice-to-CAD removes that barrier: describe the part in plain English, get a runnable script back instantly.

## Approach

1. User types a natural-language design request.
2. The request is sent to Google's Gemini API with a strict system prompt forcing clean FreeCAD Python output.
3. The app cleans up any markdown formatting from the AI response.
4. The script is shown with syntax highlighting and is downloadable as a .py file.

## Tech Stack

- Python
- Streamlit
- Google Gemini API gemini-2.5-flash
- FreeCAD

## How to Run

pip install streamlit google-generativeai
streamlit run app.py

## Why This Approach

Constraining the AI tightly with a system prompt keeps every generated script consistent and directly runnable, which matters more than flexibility for a beginner-facing CAD tool.
