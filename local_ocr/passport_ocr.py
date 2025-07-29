import pytesseract
from PIL import Image
import json
import re
import logging
from datetime import datetime
import numpy as np
import cv2
import imutils
import sys

logging.basicConfig(level=logging.INFO)

def deskew(image):
    # Convert to grayscale if not already
    if len(image.shape) == 3:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Calculate skew angle using moments
    coords = np.column_stack(np.where(image > 0))
    
    # Check if coords is empty
    if coords.size == 0:
        return image # Return original image if no text/pixels found

    angle = cv2.minAreaRect(coords)[-1]

    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    # Rotate the image to deskew
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return rotated

def clean_name(name):
    # Remove non-alphabetic characters and extra spaces, then strip
    cleaned = re.sub(r'[^A-Z\s]', '', name).strip()
    # Replace multiple spaces with a single space
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned if cleaned else "NOT_FOUND" # Return NOT_FOUND if empty after cleaning

def extract_passport_data_local(image_path):
    try:
        img_pil = Image.open(image_path)
        image = np.array(img_pil)
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        data = {
            "firstName": "NOT_FOUND",
            "fatherName": "NOT_FOUND",
            "grandfatherName": "NOT_FOUND",
            "passportNo": "NOT_FOUND",
            "nationality": "NOT_FOUND",
            "dob": "NOT_FOUND",
            "sex": "NOT_FOUND",
            "pob": "NOT_FOUND",
            "placeOfIssue": "NOT_FOUND", # Added this field
            "dateOfIssue": "NOT_FOUND",
            "dateOfExpiry": "NOT_FOUND",
        }

        # --- MRZ (Machine Readable Zone) Detection and OCR ---
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        (H, W) = gray.shape
        # Crop the bottom 25% of the image where the MRZ is typically located
        mrz_roi = gray[int(H * 0.75):, :]

        # OCR the MRZ region of interest using Tesseract
        mrzText = pytesseract.image_to_string(mrz_roi, config=r'--oem 1 --psm 4')
        mrzText = mrzText.replace(" ", "") # Remove spaces for easier parsing
        logging.info(f"OCR extracted MRZ text:\n{mrzText}")

        # --- MRZ Parsing from extracted mrzText ---
        lines = mrzText.upper().splitlines()
        mrz_candidate_lines = []
        for line in lines:
            cleaned_line = re.sub(r'[^A-Z0-9<]', '', line)
            # Heuristic for MRZ: typically 44 chars for TD3, and contains '<'
            if len(cleaned_line) >= 30 and cleaned_line.count('<') > 5:
                mrz_candidate_lines.append(cleaned_line)

        mrz_line1 = ""
        mrz_line2 = ""

        if len(mrz_candidate_lines) >= 2:
            # Prioritize lines that are exactly 44 characters long
            for i in range(len(mrz_candidate_lines) - 1):
                if len(mrz_candidate_lines[i]) == 44 and len(mrz_candidate_lines[i+1]) == 44:
                    mrz_line1 = mrz_candidate_lines[i]
                    mrz_line2 = mrz_candidate_lines[i+1]
                    break
            # Fallback if exact 44-char lines not found, but still look for P< and high < count
            if not mrz_line1 and mrz_candidate_lines[0].startswith('P<'):
                mrz_line1 = mrz_candidate_lines[0]
                if len(mrz_candidate_lines) > 1: # Take the next line as second MRZ line
                    mrz_line2 = mrz_candidate_lines[1]
        
        if not mrz_line1 and len(mrz_candidate_lines) > 0:
            mrz_line1 = mrz_candidate_lines[0]
        if not mrz_line2 and len(mrz_candidate_lines) > 1:
            mrz_line2 = mrz_candidate_lines[1]
        elif not mrz_line2 and len(mrz_candidate_lines) > 0 and len(mrz_candidate_lines[0]) > 44:
            mrz_line1 = mrz_candidate_lines[0][:44]
            mrz_line2 = mrz_candidate_lines[0][44:]


        if mrz_line1 and mrz_line2:
            logging.info(f"Detected MRZ Line 1: {mrz_line1}")
            logging.info(f"Detected MRZ Line 2: {mrz_line2}")

            # --- Parse MRZ Line 1 (TD3 format) for Names ---
            # The prompt specifies: "MRZ line 1 begins with the document code, followed by a
            # three-letter country code (ETH), then the surname. Your task is to extract the
            # letters immediately after ETH—in other words, parse out the surname starting
            # just after the 'ETH' in the MRZ"
            
            # Find the start of the surname after 'ETH'
            surname_start_index = mrz_line1.find('ETH')
            surname_mrz = ""
            if surname_start_index != -1 and len(mrz_line1) > surname_start_index + 3:
                # The surname is between 'ETH' and the first '<<'
                surname_end_delimiter_index = mrz_line1.find('<<', surname_start_index + 3)
                if surname_end_delimiter_index != -1:
                    surname_mrz = mrz_line1[surname_start_index + 3:surname_end_delimiter_index].replace('<', '').strip()
                else:
                    # Fallback if '<<' not found after ETH, take till end of line (unlikely for standard MRZ)
                    surname_mrz = mrz_line1[surname_start_index + 3:].replace('<', '').strip()

            # Extract given names part (after the first '<<')
            given_names_part_raw = ""
            first_double_chevron_index = mrz_line1.find('<<')
            if first_double_chevron_index != -1 and len(mrz_line1) > first_double_chevron_index + 2:
                given_names_part_raw = mrz_line1[first_double_chevron_index + 2:]
            
            given_names_from_mrz = " ".join(given_names_part_raw.replace('<', ' ').strip().split())

            # Initialize all name fields to NOT_FOUND
            data["firstName"] = "NOT_FOUND"
            data["fatherName"] = "NOT_FOUND"
            data["grandfatherName"] = "NOT_FOUND"

            # Extract first and father's name from given_names_from_mrz
            given_names_parts = given_names_from_mrz.split(' ')
            if len(given_names_parts) > 0 and given_names_parts[0]:
                data["firstName"] = clean_name(given_names_parts[0])
            if len(given_names_parts) > 1 and given_names_parts[1]:
                data["fatherName"] = clean_name(given_names_parts[1])
            if len(given_names_parts) > 2 and given_names_parts[2]:
                # If there are more than two given names, the rest are grandfather's name
                data["grandfatherName"] = clean_name(" ".join(given_names_parts[2:]))
            
            # --- Parse MRZ Line 2 (TD3 format) ---
            if len(mrz_line2) >= 44:
                data["passportNo"] = mrz_line2[0:9].replace('<', '')
                data["nationality"] = mrz_line2[10:13]
                
                dob_str = mrz_line2[13:19]
                sex_char = mrz_line2[20]
                expiry_str = mrz_line2[21:27]

                data["sex"] = sex_char if sex_char in ['M', 'F'] else "NOT_FOUND"

                try:
                    dob_date = datetime.strptime(dob_str, '%y%m%d')
                    # Handle century ambiguity
                    if dob_date.year > datetime.now().year:
                        dob_date = dob_date.replace(year=dob_date.year - 100)
                    data["dob"] = dob_date.strftime('%d %b %y').upper()
                except ValueError:
                    data["dob"] = "NOT_FOUND" # Set to NOT_FOUND on error

                try:
                    expiry_date = datetime.strptime(expiry_str, '%y%m%d')
                    # Handle century ambiguity
                    if expiry_date.year < datetime.now().year - 50:
                         expiry_date = expiry_date.replace(year=expiry_date.year + 100)
                    data["dateOfExpiry"] = expiry_date.strftime('%d %b %y').upper()
                    
                except ValueError:
                    data["dateOfExpiry"] = "NOT_FOUND" # Set to NOT_FOUND on error

        # --- Other Fields (less reliable, rely on visual OCR) ---
        # Perform OCR on the full image with a general PSM for other fields
        # This is done after MRZ extraction to avoid interference
        gray_full = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred_full = cv2.medianBlur(gray_full, 3)
        deskewed_full = deskew(blurred_full)
        _, thresh_full = cv2.threshold(deskewed_full, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        full_image_text = pytesseract.image_to_string(Image.fromarray(thresh_full), config=r'--oem 1 --psm 11')
        logging.info(f"OCR extracted full image text for other fields:\n{full_image_text}")

        # Place of Birth
        pob_match = re.search(r'(PLACE\s*OF\s*BIRTH|POB)\s*[:\-]?\s*([A-Z\s.,-]+)', full_image_text, re.IGNORECASE)
        if pob_match:
            data["pob"] = pob_match.group(2).strip().replace('\n', ' ')
        else:
            data["pob"] = "NOT_FOUND" # Ensure it's set to NOT_FOUND if not found

        # Place of Issue (New field)
        place_of_issue_match = re.search(r'(PLACE\s*OF\s*ISSUE|ISSUING\s*AUTHORITY|AUTHORITY)\s*[:\-]?\s*([A-Z\s.,-]+)', full_image_text, re.IGNORECASE)
        if place_of_issue_match:
            data["placeOfIssue"] = place_of_issue_match.group(2).strip().replace('\n', ' ')
        else:
            data["placeOfIssue"] = "NOT_FOUND" # Ensure it's set to NOT_FOUND if not found

        # Date of Issue
        # Look for patterns like DD MMM YY or DD MMM YYYY
        issue_date_match = re.search(r'(\d{1,2}\s*[A-Z]{3}\s*\d{2,4})', full_image_text, re.IGNORECASE)
        if issue_date_match:
            date_str = issue_date_match.group(1).upper()
            parts = date_str.split(' ')
            if len(parts[0]) == 1: # Pad day with leading zero if single digit
                parts[0] = '0' + parts[0]
            # Ensure year is 2 digits
            year_part = parts[2]
            if len(year_part) == 4:
                parts[2] = year_part[2:] # Take last two digits for YY format
            data["dateOfIssue"] = ' '.join(parts)
        else:
            data["dateOfIssue"] = "NOT_FOUND" # Set to NOT_FOUND if not found

        return data

    except Exception as e:
        logging.error(f"Error during local passport data extraction: {e}", exc_info=True)
        return None