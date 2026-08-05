#!/usr/bin/env python3
"""Streamlit frontend entry point."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("streamlit")

st.set_page_config(
    page_title=settings.app_name,
    page_icon="🤖",
    layout="wide",
)

st.title(f"{settings.app_name}")
st.caption("Plateforme d'agents IA professionnelle")

with st.sidebar:
    st.header("Navigation")
    st.write("Configuration et agents disponibles ici.")

st.info("Interface Streamlit en cours de développement.")
