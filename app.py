import os
import logging
import json
import uuid
from flask import Flask, render_template, request, jsonify, send_from_directory
from datetime import datetime
from PIL import Image
import google.generativeai as genai
from dotenv import load_dotenv
from pdf_utils import create_cv_pdf

load_dotenv()

# Load environment variables from .env file
load_dotenv()

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# Configure logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    # Serve uploaded files from the UPLOAD_FOLDER
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

def extract_passport_data_with_gemini(image_path):
    """
    Extracts passport data from an image using the Gemini AI model.
    The prompt guides the AI to extract specific fields and format them as a JSON object.
    """
    try:
        img = Image.open(image_path)
        prompt = """You are an expert passport data extraction agent. I have provided you with an image of a passport.
Your task is to accurately extract the required information and return it as a single, valid JSON object.

For names:
  - Extract the FIRST NAME, FATHER'S NAME, and GRANDFATHER'S NAME from the Machine-Readable Zone (MRZ).
  - The MRZ name format is typically SURNAME<<GIVEN<NAMES>. The GIVEN<NAMES> part often contains the first and father's name.
  - The SURNAME part may contain the grandfather's name, or it might be part of the GIVEN<NAMES> if there are multiple given names.
  - MRZ line 1 begins with the document code, followed by a three-letter country code (ETH), then the surname. Your task is to extract the letters immediately after ETH—in other words, parse out the surname starting just after the 'ETH' in the MRZ
  - If any of these name components (first, father, grandfather) are not explicitly found in the MRZ, set their value to 'NOT_FOUND'.

Prioritize the Machine-Readable Zone (MRZ) for the highest accuracy for fields like passport number, nationality, date of birth, sex, and expiry date.
For fields not in the MRZ, like 'Place of Birth', 'Place of Issue' and 'Date of Issue', use the visually printed text.
If the 'Place of Birth' is not explicitly found, set the value to 'NOT_FOUND'.
The JSON object should have the following keys:
firstName
fatherName
grandfatherName
passportNo
nationality
dob (format as DD MMM YY, e.g., 23 OCT 91)
sex (e.g., F or M)
pob (Place of Birth)
placeOfIssue
dateOfIssue (format as DD MMM YY, e.g., 06 MAY 25)
dateOfExpiry (format as DD MMM YY, e.g., 05 MAY 30)
Respond ONLY with the single, valid JSON object."""
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content([prompt, img])
        json_string = response.text.strip()
        # Clean up JSON string if it's wrapped in markdown code block
        if json_string.startswith("```json"):
            json_string = json_string.strip("```json").strip("```").strip()
        extracted_data = json.loads(json_string)
        return extracted_data
    except Exception as e:
        app.logger.error(f"Error during passport data extraction: {e}")
        return None

@app.route('/')
def index():
    # Render the main HTML page for the CV generator
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_cv():
    # Log request reception for debugging
    app.logger.info(f"Request received to generate CV")

    # 1. Save uploaded files and get form data
    passport_image = request.files['passport']
    face_image = request.files['face']
    full_body_image = request.files['full_body']
    contact_phone = request.form.get('contactPhone', '+251936987452')
    religion = request.form.get('religion', 'Muslim')
    experiences = json.loads(request.form.get('experiences', '[]'))

    # Define paths for saving uploaded images
    passport_path = os.path.join(app.config['UPLOAD_FOLDER'], passport_image.filename)
    face_path = os.path.join(app.config['UPLOAD_FOLDER'], face_image.filename)
    full_body_path = os.path.join(app.config['UPLOAD_FOLDER'], full_body_image.filename)

    # Save the uploaded image files
    passport_image.save(passport_path)
    face_image.save(face_path)
    full_body_image.save(full_body_path)

    # 2. Extract data from passport using Gemini AI
    extracted_data = extract_passport_data_with_gemini(passport_path)
    if not extracted_data:
        return "Error: Could not extract data from passport image.", 500

    # 3. Process extracted data and prepare for PDF generation
    # Calculate age from date of birth
    if 'dob' in extracted_data and extracted_data['dob'] and extracted_data['dob'] != 'NOT_FOUND':
        try:
            dob = datetime.strptime(extracted_data['dob'], '%d %b %y')
            today = datetime.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            extracted_data['age'] = str(age)
        except ValueError:
            app.logger.warning(f"Could not parse date of birth: {extracted_data['dob']}")
            extracted_data['age'] = ''
    else:
        extracted_data['age'] = ''

    # Set living town to be the same as place of birth if available
    if 'pob' in extracted_data and extracted_data['pob'] != 'NOT_FOUND':
        extracted_data['livingTown'] = extracted_data['pob']
    else:
        extracted_data['livingTown'] = ''

    # Add current CV creation date and default place of issue
    extracted_data["cvCreationDate"] = datetime.now().strftime("%d %b %Y").upper()
    extracted_data['placeOfIssue'] = 'Addis Ababa'
    
    # Define default data structure to ensure all expected fields are present
    default_data = {
        "firstName": "", "fatherName": "", "grandfatherName": "", "passportNo": "",
        "nationality": "", "dob": "", "sex": "", "pob": "", "placeOfIssue": "",
        "dateOfIssue": "", "dateOfExpiry": "", "age": "", "livingTown": "",
        "contactPhone": contact_phone, "religion": religion, "experiences": experiences
    }
    # Merge extracted data with defaults
    final_data = {**default_data, **extracted_data}

    # Construct full name from individual components
    first_name = final_data.get('firstName', '')
    father_name = final_data.get('fatherName', '')
    grandfather_name = final_data.get('grandfatherName', '')
    full_name_parts = [part for part in [first_name, father_name, grandfather_name] if part and part != 'NOT_FOUND']
    final_data['fullName'] = " ".join(full_name_parts).strip()
    
    # Log final data for PDF generation (for debugging purposes)
    app.logger.info(f"--- Data for PDF Generation ---")
    app.logger.info(json.dumps(final_data, indent=2))
    app.logger.info(f"---------------------------------")

    # 4. Generate PDF
    template_pdf_path = 'template.pdf'
    unique_id = uuid.uuid4().hex[:8]
    safe_full_name = "".join([c if c.isalnum() else '_' for c in final_data.get('fullName', 'candidate')])
    output_filename = f"{safe_full_name}_{unique_id}.pdf"
    output_pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)

    # Call the PDF utility function to create the CV
    pdf_created = create_cv_pdf(output_pdf_path, final_data, template_pdf_path, face_path, full_body_path, passport_path)

    if not pdf_created:
        return "Error: Could not create PDF.", 500

    # Return success response with download URL
    return jsonify({
        "fullName": final_data.get('fullName', 'candidate'),
        "downloadUrl": f"/uploads/{os.path.basename(output_pdf_path)}"
    })

if __name__ == '__main__':
    # Run the Flask application in debug mode (for development)
    app.run(debug=True)
