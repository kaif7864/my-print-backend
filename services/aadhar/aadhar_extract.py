import pymupdf
import re
import base64

def extract_aadhaar_details(pdf_path):
    doc = pymupdf.open(pdf_path)
    text = ""

    for page in doc:
        text += page.get_text()

    raw_text = text
    text_clean = text.replace("\n", " ")

    # ---------------- NAME ----------------
    name_match = re.search(r"\n([A-Za-z\s]+)\nजन्म तिथि/DOB", text)
    name = name_match.group(1).strip() if name_match else ""

    hindi_name_match = re.search(r"\n([\u0900-\u097F\s]+)\n[A-Za-z\s]+\nजन्म तिथि/DOB", text)
    hindi_name = hindi_name_match.group(1).strip() if hindi_name_match else ""

    # ---------------- FATHER ----------------
    father_match = re.search(r"S/O:\s*([A-Za-z\s]+?),", text)
    father_name = father_match.group(1).strip() if father_match else ""

    hindi_father_match = re.search(r"आत्मज:\s*([\u0900-\u097F\s]+?),", text)
    hindi_father = hindi_father_match.group(1).strip() if hindi_father_match else ""

    # ---------------- DOB ----------------
    dob_match = re.search(r"जन्म तिथि/DOB:\s*(\d{2}/\d{2}/\d{4})", text)
    dob = dob_match.group(1) if dob_match else ""

    # ---------------- GENDER ----------------
    gender_match = re.search(r"(पुरुष/ MALE|महिला/ FEMALE|MALE|FEMALE)", text, re.IGNORECASE)
    gender_key = "M"
    if gender_match:
        g_raw = gender_match.group(1).upper()
        if "FEMALE" in g_raw or "महिला" in g_raw:
            gender_key = "F"

    # ---------------- AADHAAR NUMBER ----------------
    aadhaar_numbers = re.findall(r"\b\d{4}\s\d{4}\s\d{4}\b", text)
    aadhaar_number = aadhaar_numbers[0] if aadhaar_numbers else ""

    # ---------------- VID ----------------
    vid_match = re.search(r"VID\s*:\s*(\d{4}\s\d{4}\s\d{4}\s\d{4})", text)
    vid_number = vid_match.group(1) if vid_match else ""

    # ---------------- VERTICAL DATE FIX ----------------
    compact_text = raw_text.replace("\n", "").replace(" ", "")
    issued_match = re.search(r"Aadhaarno\.issued:(\d{2}/\d{2}/\d{4})", compact_text)
    issued_date = issued_match.group(1) if issued_match else ""

    details_as_on_match = re.search(r"Details as on:\s*(\d{2}/\d{2}/\d{4})", text)
    details_as_on = details_as_on_match.group(1) if details_as_on_match else ""

    # ---------------- ADDRESS ----------------
    address_match = re.search(r"Address:\s*(.*?)Uttarakhand", text, re.DOTALL)
    address =  address_match.group(1).strip() + " Uttarakhand 249407" if address_match else ""

    hindi_address_match = re.search(r"पता:\s*(.*?)249407", text, re.DOTALL)
    hindi_address = "पता:\n" + hindi_address_match.group(1).strip() + "249407" if hindi_address_match else ""

    # ---------------- SMART PHOTO EXTRACTION ----------------
# ... (बाकी कोड समान रहेगा)

    # ---------------- SMART PHOTO EXTRACTION (IMPROVED) ----------------
    photo_base64 = ""
    target_xref = None

    for page in doc:
        images = page.get_images(full=True)
        for img in images:
            xref = img[0]
            base_image = doc.extract_image(xref)
            width = base_image["width"]
            height = base_image["height"]
            
            # 1. QR कोड को हटाने के लिए: QR कोड का aspect ratio लगभग 1:1 (Square) होता है
            aspect_ratio = width / height
            
            # 2. फिल्टर: फोटो आमतौर पर 0.7 से 0.9 के अनुपात में होती है (लंबी होती है चौड़ी नहीं)
            # साथ ही बहुत छोटी या बहुत बड़ी इमेज को छोड़ दें
            if 2000 < (width * height) < 100000:
                if 0.6 < aspect_ratio < 1.0: # यह एक पोर्ट्रेट फोटो की पहचान है
                    target_xref = xref
                    # पहली ऐसी इमेज मिलते ही ब्रेक कर सकते हैं जो मापदंडों पर खरी उतरे
                    break 

    if target_xref:
        selected_img = doc.extract_image(target_xref)
        photo_base64 = base64.b64encode(selected_img["image"]).decode("utf-8")

# ... (बाकी कोड समान रहेगा)
    # print("Final Selected Image Area:", largest_area)

    # ---------------- FINAL RETURN ----------------
    return {
        "name_english": name,
        "name_hindi": hindi_name,
        "father_english": father_name,
        "father_hindi": hindi_father,
        "dob": dob,
        "gender": gender_key,
        "aadhaar_number": aadhaar_number,
        "vid_number": vid_number,
        "issued_date": issued_date,
        "details_as_on": details_as_on,
        "address_english": address,
        "address_hindi": hindi_address,
        "photo_base64": photo_base64,
        "raw_text": raw_text
    }