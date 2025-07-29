# Foreign Employment Agency CV Generator

[GitHub Repository](https://github.com/sualh1999/ai_cv_generator-)

This web application is designed for foreign employment agencies to streamline the process of creating CVs for domestic workers. It uses AI to automatically extract candidate information from a scanned passport image and populates it into a pre-defined PDF template. The application also embeds the candidate's face and full-body photos into the CV, creating a complete and professional document.

## Features

- **AI-Powered Data Extraction:** Automatically extracts key information (name, passport number, date of birth, etc.) from passport images using Google's Gemini AI or OpenRouter.
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

4.  **Create a `.env` file** by copying the example file:
    ```bash
    cp .env.example .env
    ```

5.  **Add your API keys** to the `.env` file. You can get your API keys from:
    - [Google AI Studio](https://aistudio.google.com/)
    - [OpenRouter](https://openrouter.ai/)

    Your `.env` file should look like this:
    ```
    GEMINI_API_KEY_1=YOUR_GEMINI_API_KEY_1
    GEMINI_API_KEY_2=YOUR_GEMINI_API_KEY_2
    OPENROUTER_API_KEY=YOUR_OPENROUTER_API_KEY
    ```

6.  **Run the application:**
    ```bash
    python app.py
    ```

7.  **Open your browser** and navigate to `http://127.0.0.1:5000` to use the application.

## Security

This application includes several security features to protect against common vulnerabilities:

- **Environment Variables:** All API keys and sensitive information are stored in a `.env` file and are not hardcoded in the application.
- **File Uploads:** The application validates file uploads to ensure that only allowed file types (PNG, JPG, JPEG) are accepted. Filenames are also sanitized to prevent directory traversal attacks.
- **Debug Mode:** Debug mode is disabled by default to prevent the exposure of sensitive information in a production environment.