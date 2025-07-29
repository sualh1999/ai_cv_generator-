import os
import logging
import json
import uuid
import requests
import base64
from flask import Flask, render_template, request, jsonify, send_from_directory, session, url_for, redirect, abort
from werkzeug.utils import secure_filename
from datetime import datetime
from PIL import Image
import google.generativeai as genai
from dotenv import load_dotenv
from pdf_utils import create_cv_pdf
from local_ocr.passport_ocr import extract_passport_data_local


# Load environment variables from .env file
load_dotenv()

# Configure Gemini API
GEMINI_API_KEY_1 = os.getenv("GEMINI_API_KEY_1")
GEMINI_API_KEY_2 = os.getenv("GEMINI_API_KEY_2")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")


# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.secret_key = os.urandom(24)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/clear_session')
def clear_session():
    session.pop('cv_data', None)
    session.pop('output_pdf_path', None)
    return redirect(url_for('index'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    # Serve uploaded files from the UPLOAD_FOLDER
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

def extract_passport_data_with_gemini(image_path):
    """
    Extracts passport data from an image using the Gemini AI model.
    The prompt guides the AI to extract specific fields and format them as a JSON object.
    """
    api_keys = [GEMINI_API_KEY_1, GEMINI_API_KEY_2]
    
    for i, api_key in enumerate(api_keys):
        if not api_key:
            app.logger.warning(f"API key {i+1} is not set. Skipping.")
            continue

        try:
            app.logger.info(f"Attempting to use API key {i+1}")
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            img = Image.open(image_path)
            prompt = '''You are an expert passport data extraction agent. I have provided you with an image of a passport.
Your task is to accurately extract the required information and return it as a single, valid JSON object.

For names, pay close attention to the Machine-Readable Zone (MRZ) format:
  - The MRZ for Ethiopian passports is structured as SURNAME<<FIRSTNAME<FATHERNAME.
  - The SURNAME is the grandfather's name.
  - The FIRSTNAME is the person's first name.
  - The FATHERNAME is the father's name.
  - Example: If the MRZ is "ETHDOE<<JOHN<DOE", then:
    - grandfatherName: "DOE"
    - firstName: "JOHN"
    - fatherName: "DOE"
  - Extract the FIRST NAME, FATHER'S NAME, and GRANDFATHER'S NAME based on this structure.
  - If any of these name components are not explicitly found in the MRZ, set their value to 'NOT_FOUND'.

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
Respond ONLY with the single, valid JSON object.'''
            
            response = model.generate_content([prompt, img], request_options={'timeout': 60})
            json_string = response.text.strip()

            if json_string.startswith("```json"):
                json_string = json_string.strip("```json").strip("```").strip()
            
            extracted_data = json.loads(json_string)
            app.logger.info(f"Successfully extracted data with API key {i+1}")
            return extracted_data

        except Exception as e:
            app.logger.error(f"Failed to use API key {i+1}: {e}")
            continue

    app.logger.error("All API keys failed. Could not extract passport data.")
    return None

def extract_passport_data_with_openrouter(image_path):
    if not OPENROUTER_API_KEY:
        app.logger.error("OpenRouter API key not set.")
        return None

    try:
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')

        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:5000",
                "X-Title": "CV Generator"
            },
            json={
                "model": "google/gemini-flash-1.5",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """You are an expert passport data extraction agent. I have provided you with an image of a passport.
Your task is to accurately extract the required information and return it as a single, valid JSON object.

For names, pay close attention to the Machine-Readable Zone (MRZ) format:
  - The MRZ for Ethiopian passports is structured as SURNAME<<FIRSTNAME<FATHERNAME.
  - The SURNAME is the grandfather's name.
  - The FIRSTNAME is the person's first name.
  - The FATHERNAME is the father's name.
  - Example: If the MRZ is "ETHDOE<<JOHN<DOE", then:
    - grandfatherName: "DOE"
    - firstName: "JOHN"
    - fatherName: "DOE"
  - Extract the FIRST NAME, FATHER'S NAME, and GRANDFATHER'S NAME based on this structure.
  - If any of these name components are not explicitly found in the MRZ, set their value to 'NOT_FOUND'.

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
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_data}"
                                }
                            }
                        ]
                    }
                ]
            },
            timeout=60
        )
        response.raise_for_status()
        json_response = response.json()
        
        app.logger.debug(f"Full OpenRouter response: {json.dumps(json_response, indent=2)}")

        content_string = json_response.get('choices', [{}])[0].get('message', {}).get('content', '').strip()
        
        app.logger.debug(f"Content from OpenRouter: '{content_string}'")

        if content_string.startswith("```json"):
            content_string = content_string.strip("```json").strip("```").strip()

        if not content_string:
            app.logger.error("OpenRouter response content is empty.")
            return None

        extracted_data = json.loads(content_string)
        app.logger.info("Successfully extracted data with OpenRouter.")
        return extracted_data
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Error calling OpenRouter API: {e}")
        if hasattr(e, 'response') and e.response is not None:
            app.logger.error(f"Response content: {e.response.text}")
        return None
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        app.logger.error(f"Error parsing OpenRouter response: {e}")
        # Also log the problematic content if possible
        if 'content_string' in locals():
            app.logger.error(f"Problematic content: {content_string}")
        return None

@app.route('/')
def index():
    cv_data = session.get('cv_data', {})
    download_url = None
    if 'output_pdf_path' in session:
        output_pdf_path = session.get('output_pdf_path')
        download_url = url_for('uploaded_file', filename=os.path.basename(output_pdf_path))
    return render_template('index.html', cv_data=cv_data, download_url=download_url)

@app.route('/edit')
def edit_cv():
    cv_data = session.get('cv_data', {})
    return render_template('edit_cv.html', cv_data=cv_data)

@app.route('/generate', methods=['POST'])
def generate_cv():
    app.logger.info("Request received to generate CV")

    try:
        if request.form.get('regenerate') == 'true':
            final_data = session.get('cv_data', {})
            # Preserve image paths from session if not explicitly sent in form
            face_path = final_data.get('face_image_path')
            full_body_path = final_data.get('full_body_image_path')
            passport_path = final_data.get('passport_image_path')

            app.logger.debug(f"final_data before update: {final_data}")
            form_data_dict = request.form.to_dict()
            app.logger.debug(f"Form data received: {form_data_dict}")
            final_data.update(form_data_dict)
            final_data['experiences'] = json.loads(request.form.get('experiences', '[]'))
            app.logger.debug(f"final_data after update: {final_data}")

            # Update paths if they were sent in the form (e.g., from hidden fields)
            if request.form.get('face_image_path'):
                face_path = request.form.get('face_image_path')
            if request.form.get('full_body_image_path'):
                full_body_path = request.form.get('full_body_image_path')
            if request.form.get('passport_image_path'):
                passport_path = request.form.get('passport_image_path')
        else:
            passport_image = request.files.get('passport')
            face_image = request.files.get('face')
            full_body_image = request.files.get('full_body')

            if not all([passport_image, face_image, full_body_image]) or \
               not allowed_file(passport_image.filename) or \
               not allowed_file(face_image.filename) or \
               not allowed_file(full_body_image.filename):
                return jsonify({"message": "Missing one or more required image files, or file type not allowed."}), 400

            passport_filename = secure_filename(passport_image.filename)
            face_filename = secure_filename(face_image.filename)
            full_body_filename = secure_filename(full_body_image.filename)

            passport_path = os.path.join(app.config['UPLOAD_FOLDER'], passport_filename)
            face_path = os.path.join(app.config['UPLOAD_FOLDER'], face_filename)
            full_body_path = os.path.join(app.config['UPLOAD_FOLDER'], full_body_filename)

            passport_image.save(passport_path)
            face_image.save(face_path)
            full_body_image.save(full_body_path)

            extraction_method = request.form.get('extractionMethod', 'ai') # Default to AI

            if extraction_method == 'ai':
                extracted_data = extract_passport_data_with_gemini(passport_path)
            elif extraction_method == 'openrouter':
                extracted_data = extract_passport_data_with_openrouter(passport_path)
            elif extraction_method == 'local_ocr':
                extracted_data = extract_passport_data_local(passport_path)
            else:
                extracted_data = None

            if not extracted_data:
                return jsonify({"message": f"Could not extract data from passport using {extraction_method}."}), 500
            

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

            if 'pob' in extracted_data and extracted_data['pob'] != 'NOT_FOUND':
                extracted_data['livingTown'] = extracted_data['pob']
            else:
                extracted_data['livingTown'] = ''

            extracted_data["cvCreationDate"] = datetime.now().strftime("%d %b %Y").upper()
            extracted_data['placeOfIssue'] = 'Addis Ababa'
            
            default_data = {
                "firstName": "", "fatherName": "", "grandfatherName": "", "passportNo": "",
                "nationality": "", "dob": "", "sex": "", "pob": "", "placeOfIssue": "",
                "dateOfIssue": "", "dateOfExpiry": "", "age": "", "livingTown": "",
                "contactPhone": request.form.get('contactPhone', '+251936987452'), 
                "religion": request.form.get('religion', 'Muslim'), 
                "experiences": json.loads(request.form.get('experiences', '[]'))
            }
            final_data = {**default_data, **extracted_data}

        # Always reconstruct fullName from its components after data is finalized
        first_name = final_data.get('firstName', '')
        father_name = final_data.get('fatherName', '')
        grandfather_name = final_data.get('grandfatherName', '')
        full_name_parts = [part for part in [first_name, father_name, grandfather_name] if part and part != 'NOT_FOUND']
        final_data['fullName'] = " ".join(full_name_parts).strip()
        
        session['cv_data'] = final_data
        session['cv_data']['face_image_path'] = face_path
        session['cv_data']['full_body_image_path'] = full_body_path
        session['cv_data']['passport_image_path'] = passport_path

        template_pdf_path = 'template.pdf'
        unique_id = uuid.uuid4().hex[:8]
        safe_full_name = "".join([c if c.isalnum() else '_' for c in final_data.get('fullName', 'candidate')])
        output_filename = f"{safe_full_name}_{unique_id}.pdf"
        output_pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)

        pdf_created = create_cv_pdf(output_pdf_path, final_data, template_pdf_path, face_path, full_body_path, passport_path)

        if not pdf_created:
            return jsonify({"message": "Failed to create the PDF. Please check the logs for more details."}), 500

        if request.form.get('regenerate') == 'true':
            session['output_pdf_path'] = output_pdf_path
            return redirect(url_for('index'))

        return jsonify({
            "fullName": final_data.get('fullName', 'candidate'),
            "downloadUrl": f"/uploads/{os.path.basename(output_pdf_path)}",
            "editUrl": url_for('edit_cv'),
            "cv_data": final_data
        })

    except Exception as e:
        app.logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        return jsonify({"message": "An unexpected server error occurred. Please try again later."}), 500

if __name__ == '__main__':
    app.run(debug=False)
