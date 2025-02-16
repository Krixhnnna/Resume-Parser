# Resume Parser with AI Enhancement

This project extracts text from a PDF resume and structures it into a well-formatted resume with missing details intelligently generated using Google's Gemini AI.

## Features
- Extracts text from a PDF resume.
- Uses Google Gemini AI to structure and enhance the data.
- Saves the structured resume in `Structured_data.txt`.

## Prerequisites
- Python 3.x
- Required Python Libraries:
  ```sh
  pip install pdfplumber google-generativeai
  ```
- Google Gemini API Key

## Usage
1. Clone the repository:
   ```sh
   git clone https://github.com/Krixhnnna/Resume-Parser
   cd resume-parser
   ```
2. Add your Google Gemini API key inside the script:
   ```python
   genai.configure(api_key="YOUR_API_KEY")
   ```
3. Run the script:
   ```sh
   python script.py
   ```
4. Enter the PDF file path when prompted.
5. Extracted text will be saved in `output/data.txt`.
6. The structured resume will be saved in `output/Structured_data.txt`.

## File Structure
```
resume-parser/
│-- script.py
│-- README.md
│-- output/
    │-- data.txt
    │-- Structured_data.txt
```

## Output Format
```
Name:
Location: City, State
Phone No:
LinkedIn:
GitHub:
Summary: (AI-generated summary)
Experiences: (Internships or Full-time)
Projects: (List with descriptions)
Certifications: (Relevant certificates)
Technical Skills:
Education: (Degree, College, Date)
Other Relevant Details:
```

## License
This project is open-source and available under the MIT License.

## Author
- **Krishna Pandey** - [GitHub](https://github.com/Krixhnnna/Resume-Parser)

