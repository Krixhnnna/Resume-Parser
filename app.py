import pdfplumber
import os
import google.generativeai as genai

genai.configure(api_key="YOUR_API_KEY")

def extract_text_from_pdf(pdf_path, output_folder="output", output_file="data.txt"):
    os.makedirs(output_folder, exist_ok=True)
    output_path = os.path.join(output_folder, output_file)
    
    with pdfplumber.open(pdf_path) as pdf:
        text = "".join(page.extract_text() or "" for page in pdf.pages)
    
    with open(output_path, "w", encoding="utf-8") as file:
        file.write(text)
    
    print(f"Text extracted and saved to {output_path}")
    return text

def generate_structured_resume(text, output_folder="output", output_file="Structured_data.txt"):
    model = genai.GenerativeModel("gemini-pro")
    prompt = f"""Extract and structure the following resume data:
    {text}
    Format it in this structured manner:
    Name:
    Location: city, State
    Phone No:
    LinkedIn:
    GitHub:
    Summary: Generate a small paragraph using AI after reading all the data.
    Experiences: Internships or Full-time
    All Projects list with Description
    Certifications / Certificates
    Technical Skills:
    Education with degree, college name, and date
    Also mention some extra data which is not in the structure but given in the resume."""
    
    response = model.generate_content(prompt)
    structured_data = response.text
    
    output_path = os.path.join(output_folder, output_file)
    with open(output_path, "w", encoding="utf-8") as file:
        file.write(structured_data)
    
    print(f"Structured resume saved to {output_path}")

if __name__ == "__main__":
    pdf_path = input("Enter the path of the resume PDF: ").strip()
    if os.path.exists(pdf_path) and pdf_path.lower().endswith(".pdf"):
        resume_text = extract_text_from_pdf(pdf_path)
        generate_structured_resume(resume_text)
    else:
        print("Invalid file. Please provide a valid PDF.")
