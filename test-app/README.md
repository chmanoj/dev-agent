# Streamlit Hello World Multi-Page App

A simple multi-page Streamlit application demonstrating basic functionality and project structure using uv and pyproject.toml.

## Features

- **Multi-page navigation**: Home, About, and Contact pages
- **Interactive components**: Forms, buttons, metrics, and more
- **Modern Python tooling**: Uses uv for dependency management
- **Clean project structure**: Organized with pyproject.toml configuration

## Project Structure

```
├── main.py              # Home page (entry point)
├── pages/
│   ├── 1_About.py       # About page
│   └── 2_Contact.py     # Contact page with form
├── pyproject.toml       # Project configuration
└── README.md           # This file
```

## Setup and Installation

1. **Install uv** (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Install dependencies**:
   ```bash
   uv sync
   ```

3. **Run the application**:
   ```bash
   uv run streamlit run main.py
   ```

4. **Open your browser** to `http://localhost:8501`

## Usage

- Navigate between pages using the sidebar
- Try the interactive elements on each page
- Fill out the contact form to see form handling in action

## Development

To add new pages:
1. Create a new Python file in the `pages/` directory
2. Name it with a number prefix (e.g., `3_NewPage.py`)
3. Streamlit will automatically detect and add it to the navigation

## Dependencies

- **streamlit**: Web app framework
- **python**: 3.8+

See `pyproject.toml` for complete dependency list.