# Foreign Employment Agency CV Generator

This web application is designed for foreign employment agencies to streamline the process of creating CVs for domestic workers (maids). It uses AI to automatically extract candidate information from a scanned passport image and populates it into a pre-defined PDF template. The application also embeds the candidate's face and full-body photos into the CV, creating a complete and professional document.

## Features

- **AI-Powered Data Extraction:** Automatically extracts key information (name, passport number, date of birth, etc.) from passport images using Google's Gemini AI.
- **Automated PDF Generation:** Fills the extracted data into a standardized CV template.
- **Image Embedding:** Inserts the candidate's face and full-body photos into the correct positions on the CV.
- **User-Friendly Interface:** A simple web interface for uploading images and generating CVs.

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd cv_generator
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

## Running the Application

1.  **Install Gunicorn (for production deployment):**
    ```bash
    pip install gunicorn
    ```

2.  **Start the Gunicorn server (for production):**
    ```bash
    gunicorn -w 4 "app:app"
    ```
    (Replace `4` with the number of worker processes appropriate for your server. A common rule of thumb is `2 * number_of_cores + 1`.)

3.  **Alternatively, for local development, start the Flask development server:**
    ```bash
    flask run
    ```

4.  **Open your browser** and navigate to `http://127.0.0.1:5000` to use the application.
