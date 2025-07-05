import fitz  # PyMuPDF
from PIL import Image
import logging

logging.basicConfig(level=logging.WARNING)

def create_cv_pdf(output_path, data, template_path, face_image_path, full_body_image_path, passport_image_path):
    """
    Generates a CV in PDF format by filling a template with provided data and images.

    Args:
        output_path (str): The path where the generated PDF will be saved.
        data (dict): A dictionary containing all the text data to be inserted into the PDF.
        template_path (str): The path to the base PDF template.
        face_image_path (str): The path to the candidate's face image.
        full_body_image_path (str): The path to the candidate's full body image.
        passport_image_path (str): The path to the candidate's passport image.

    Returns:
        bool: True if the PDF was created successfully, False otherwise.
    """
    try:
        template_doc = fitz.open(template_path)
        for page_num, page in enumerate(template_doc):
            if page_num == 0:
                # Define field coordinates for the first page (x_left, y_top, x_right, y_bottom)
                field_coords = {
                    "fullName": {"rect": (240, 197, 476, 207), "font_size": 9},
                    "passportNo": {"rect": (375, 225, 508, 235), "font_size": 9},
                    "dob": {"rect": (140, 248, 258, 261), "font_size": 9},
                    "age": {"rect": (140, 264, 258, 281), "font_size": 9},
                    "pob": {"rect": (140, 282, 258, 292), "font_size": 9},
                    "livingTown": {"rect": (140, 298, 258, 308), "font_size": 9},
                    "dateOfIssue": {"rect": (375, 236, 508, 246), "font_size": 9},
                    "placeOfIssue": {"rect": (375, 247, 508, 261), "font_size": 9},
                    "dateOfExpiry": {"rect": (375, 263, 508, 281), "font_size": 9},
                    "cvCreationDate": {"rect": (349, 123, 481, 131), "font_size": 9},
                    "contactPhone": {"rect": (284, 133, 482, 142), "font_size": 9},
                    "religion": {"rect": (140, 237, 258, 246), "font_size": 9},
                }

                for field_name, field_data in field_coords.items():
                    if field_name in data:
                        text_to_insert = data[field_name]
                        if text_to_insert is None or text_to_insert == 'NOT_FOUND':
                            text_to_insert = ""

                        # PyMuPDF uses (x, y) for the bottom-left corner of the text.
                        # We use the bottom of the rectangle (y_bottom) as the baseline for text.
                        x_coord = field_data["rect"][0] + 5  # Small offset from left edge
                        y_coord = field_data["rect"][3]     # Use y_bottom of the rect for text baseline
                        font_size = field_data["font_size"]
                        
                        page.insert_text((x_coord, y_coord), text_to_insert, fontsize=font_size, fontname="helv")
                        logging.info(f"Inserted text '{text_to_insert}' for {field_name} at ({x_coord}, {y_coord}) on page {page_num + 1}.")

                if 'experiences' in data and data['experiences']:
                    # Coordinates for experience fields on the PDF
                    experience_coords = [
                        {"country": (140, 562, 258, 574), "year": (140, 578, 258, 590)},
                        {"country": (140, 596, 257, 608), "year": (140, 613, 259, 625)},
                        {"country": (140, 630, 258, 642), "year": (140, 647, 259, 659)}
                    ]
                    experience_font_size = 9
                    font_name = "helv"

                    for i, exp in enumerate(data['experiences']):
                        if i < len(experience_coords):
                            country_text = exp.get('country', '')
                            period_text = exp.get('period', '')
                            if period_text:
                                period_text += " Year" if period_text == "1" else " Years"

                            def insert_centered_text(rect_coords, text):
                                """
                                Helper function to insert text centered within a given rectangle.
                                """
                                rect = fitz.Rect(rect_coords)
                                text_length = fitz.get_text_length(text, fontname=font_name, fontsize=experience_font_size)
                                rect_width = rect.x1 - rect.x0
                                # Calculate x-coordinate for centering
                                x = rect.x0 + (rect_width - text_length) / 2
                                # Calculate y-coordinate for baseline, with a small offset from the bottom of the rect
                                y = rect.y1 - 3
                                page.insert_text((x, y), text, fontsize=experience_font_size, fontname=font_name)

                            insert_centered_text(experience_coords[i]["country"], country_text)
                            logging.info(f"Inserted experience country '{country_text}' at {fitz.Rect(experience_coords[i]['country'])} on page {page_num + 1}.")
                            insert_centered_text(experience_coords[i]["year"], period_text)
                            logging.info(f"Inserted experience period '{period_text}' at {fitz.Rect(experience_coords[i]['year'])} on page {page_num + 1}.")

                # Image insertion logic for Face and Full-Body images
                # Face Image
                face_img_x, face_img_y_top, face_img_x2, face_img_y2 = 30, 122, 172, 196
                face_field_width = face_img_x2 - face_img_x
                face_field_height = face_img_y2 - face_img_y_top
                
                original_face_width, original_face_height = Image.open(face_image_path).size

                # Calculate aspect ratios to maintain image proportions
                face_aspect_ratio = original_face_width / original_face_height
                face_field_aspect_ratio = face_field_width / face_field_height

                # Determine new dimensions to fit within the field while maintaining aspect ratio
                if face_aspect_ratio > face_field_aspect_ratio:
                    new_face_width = face_field_width
                    new_face_height = new_face_width / face_aspect_ratio
                else:
                    new_face_height = face_field_height
                    new_face_width = new_face_height * face_aspect_ratio

                # Ensure image doesn't exceed its original size if it's smaller than the field
                if new_face_width > original_face_width or new_face_height > original_face_height:
                    new_face_width = original_face_width
                    new_face_height = original_face_height

                # Calculate offsets to center the image within its field
                face_x_offset = face_img_x + (face_field_width - new_face_width) / 2
                face_y_offset = face_img_y_top + (face_field_height - new_face_height) / 2 # PyMuPDF y is from top

                page.insert_image(fitz.Rect(face_x_offset, face_y_offset, face_x_offset + new_face_width, face_y_offset + new_face_height), filename=face_image_path)
                logging.info(f"Face image drawn at ({face_x_offset}, {face_y_offset}) with size ({new_face_width}, {new_face_height}).")

                # Full-Body Image (similar logic as Face Image)
                full_body_img_x, full_body_img_y_top, full_body_img_x2, full_body_img_y2 = 312, 283, 552, 684
                full_body_field_width = full_body_img_x2 - full_body_img_x
                full_body_field_height = full_body_img_y2 - full_body_img_y_top

                original_full_body_width, original_full_body_height = Image.open(full_body_image_path).size

                full_body_aspect_ratio = original_full_body_width / original_full_body_height
                full_body_field_aspect_ratio = full_body_field_width / full_body_field_height

                if full_body_aspect_ratio > full_body_field_aspect_ratio:
                    new_full_body_width = full_body_field_width
                    new_full_body_height = new_full_body_width / full_body_aspect_ratio
                else:
                    new_full_body_height = full_body_field_height
                    new_full_body_width = new_full_body_height * full_body_aspect_ratio

                if new_full_body_width > original_full_body_width or new_full_body_height > original_full_body_height:
                    new_full_body_width = original_full_body_width
                    new_full_body_height = original_full_body_height

                full_body_x_offset = full_body_img_x + (full_body_field_width - new_full_body_width) / 2
                full_body_y_offset = full_body_img_y_top + (full_body_field_height - new_full_body_height) / 2

                page.insert_image(fitz.Rect(full_body_x_offset, full_body_y_offset, full_body_x_offset + new_full_body_width, full_body_y_offset + new_full_body_height), filename=full_body_image_path)
                logging.info(f"Full-body image drawn at ({full_body_x_offset}, {full_body_y_offset}) with size ({new_full_body_width}, {new_full_body_height}).")

            if page_num == 1:
                # Passport Image insertion logic
                passport_img_x, passport_img_y_top, passport_img_x2, passport_img_y2 = 30, 130, 550, 750
                passport_field_width = passport_img_x2 - passport_img_x
                passport_field_height = passport_img_y2 - passport_img_y_top

                original_passport_width, original_passport_height = Image.open(passport_image_path).size

                passport_aspect_ratio = original_passport_width / original_passport_height
                passport_field_aspect_ratio = passport_field_width / passport_field_height

                if passport_aspect_ratio > passport_field_aspect_ratio:
                    new_passport_width = passport_field_width
                    new_passport_height = new_passport_width / passport_aspect_ratio
                else:
                    new_passport_height = passport_field_height
                    new_passport_width = new_passport_height * passport_aspect_ratio

                if new_passport_width > original_passport_width or new_passport_height > original_passport_height:
                    new_passport_width = original_passport_width
                    new_passport_height = original_passport_height

                passport_x_offset = passport_img_x + (passport_field_width - new_passport_width) / 2
                passport_y_offset = passport_img_y_top + (passport_field_height - new_passport_height) / 2

                page.insert_image(fitz.Rect(passport_x_offset, passport_y_offset, passport_x_offset + new_passport_width, passport_y_offset + new_passport_height), filename=passport_image_path)
                logging.info(f"Passport image drawn at ({passport_x_offset}, {passport_y_offset}) with size ({new_passport_width}, {new_passport_height}).")

        template_doc.save(output_path)
        template_doc.close()
        logging.info(f"PyMuPDF PDF saved to: {output_path}")
        return True
    except Exception as e:
        logging.error(f"Error creating PDF: {e}")
        return False
