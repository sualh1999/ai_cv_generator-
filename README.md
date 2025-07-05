# Foreign Employment Agency CV Generator

[GitHub Repository](https://github.com/sualh1999/ai_cv_generator-)


This web application is designed for foreign employment agencies to streamline the process of creating CVs for domestic workers (maids). It uses AI to automatically extract candidate information from a scanned passport image and populates it into a pre-defined PDF template. The application also embeds the candidate's face and full-body photos into the CV, creating a complete and professional document.

## Features

- **AI-Powered Data Extraction:** Automatically extracts key information (name, passport number, date of birth, etc.) from passport images using Google's Gemini AI.
- **Automated PDF Generation:** Fills the extracted data into a standardized CV template.
- **Image Embedding:** Inserts the candidate's face and full-body photos into the correct positions on the CV.
- **User-Friendly Interface:** A simple web interface for uploading images and generating CVs.

## Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/sualh1999/ai_cv_generator-
    cd ai_cv_generator-
    ```

2.  **Create a virtual environment and activate it:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install the required packages:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Create a `.env` file** in the root of the project and add your Gemini API key:
    ```
    GEMINI_API_KEY="YOUR_API_KEY"
    ```

5.  **Run the application:**
    ```bash
    python app.py
    ```



2.  **Open your browser** and navigate to `http://127.0.0.1:5000` to use the application.

