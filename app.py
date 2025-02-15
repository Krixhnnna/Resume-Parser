from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import fitz  # PyMuPDF
import re
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Enhanced HTML Template with better CSS
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Resume Builder</title>
    <style>
        :root {
            --primary: #2b2d42;
            --secondary: #8d99ae;
            --light: #edf2f4;
        }
        * { box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f8f9fa; 
        }
        .container {
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
        }
        h1 { 
            color: var(--primary);
            text-align: center;
            margin-bottom: 40px;
        }
        .section {
            margin-bottom: 30px;
            padding: 20px;
            border: 1px solid #eee;
            border-radius: 8px;
        }
        .form-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
        }
        input, textarea, button {
            width: 100%;
            padding: 12px;
            margin: 8px 0;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        button {
            background: var(--primary);
            color: white;
            border: none;
            cursor: pointer;
            transition: 0.3s;
        }
        button:hover {
            opacity: 0.9;
            transform: translateY(-1px);
        }
        .add-btn {
            background: var(--secondary);
            width: auto;
            padding: 8px 20px;
        }
        .section-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        .section-title {
            color: var(--primary);
            margin: 0;
        }
        .dynamic-field {
            margin-bottom: 15px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 6px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Resume Builder</h1>
        
        <div class="section">
            <h2 class="section-title">Import from Resume</h2>
            <form id="upload-form" enctype="multipart/form-data">
                <input type="file" id="resume" accept="application/pdf" required>
                <button type="submit">Parse Resume</button>
            </form>
        </div>

        <form id="manual-form">
            <div class="section">
                <h2 class="section-title">Basic Information</h2>
                <div class="form-grid">
                    <input type="text" id="name" placeholder="Full Name">
                    <input type="email" id="email" placeholder="Email">
                    <input type="text" id="linkedin" placeholder="LinkedIn URL">
                    <input type="tel" id="phone" placeholder="Phone Number">
                    <input type="text" id="github" placeholder="GitHub URL">
                    <input type="text" id="location" placeholder="Location">
                </div>
                <textarea id="summary" placeholder="Professional Summary" rows="4"></textarea>
            </div>

            <!-- Dynamic Sections -->
            <div class="section" id="work-section">
                <div class="section-header">
                    <h2 class="section-title">Work Experience</h2>
                    <button type="button" class="add-btn" onclick="addDynamicField('work')">+ Add Experience</button>
                </div>
                <div id="work-fields"></div>
            </div>

            <!-- Similar structure for other sections (Projects, Education, etc.) -->
        </form>
    </div>

    <script>
        // Enhanced JavaScript to handle dynamic fields
        function addDynamicField(type) {
            const field = document.createElement('div');
            field.className = 'dynamic-field';
            field.innerHTML = `
                <input type="text" placeholder="${type.replace('-', ' ')} Title">
                <textarea placeholder="Details" rows="3"></textarea>
                <button type="button" onclick="this.parentElement.remove()">Remove</button>
            `;
            document.getElementById(`${type}-fields`).appendChild(field);
        }

        // Modified fillForm function to handle dynamic data
        function fillForm(data) {
            // Basic fields
            ['name', 'email', 'linkedin', 'phone', 'github', 'location', 'summary'].forEach(id => {
                if (data[id]) document.getElementById(id).value = data[id];
            });

            // Dynamic fields
            ['work', 'education', 'projects'].forEach(type => {
                if (data[type]) {
                    data[type].forEach(item => {
                        addDynamicField(type);
                        const fields = document.getElementById(`${type}-fields`).lastChild;
                        fields.children[0].value = item.title;
                        fields.children[1].value = item.details;
                    });
                }
            });
        }
    </script>
</body>
</html>
'''

# Enhanced PDF parsing function
def parse_resume(text):
    data = {}
    
    # Name with multiple possible patterns
    name_match = re.search(r"(?m)^((?:[A-Z][a-z]+\s?){2,4})$", text)
    if not name_match:
        name_match = re.search(r"(?i)\bname:\s*((?:[A-Z][a-z]+\s?){2,4})", text)
    data["name"] = name_match.group(1).strip() if name_match else ""

    # Email
    email_match = re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", text)
    data["email"] = email_match.group() if email_match else ""

    # Phone numbers with various formats
    phone_match = re.search(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", text)
    data["phone"] = phone_match.group().strip() if phone_match else ""

    # Social profiles
    data["linkedin"] = re.findall(r"(https?://)?(www\.)?linkedin\.com/\S+", text)[-1][0] if re.findall(r"linkedin\.com", text) else ""
    data["github"] = re.findall(r"(https?://)?(www\.)?github\.com/\S+", text)[-1][0] if re.findall(r"github\.com", text) else ""

    # Location (more flexible matching)
    location_match = re.search(r"(?mi)(address|location|based in):?[\s-]*([^\n]+)", text)
    data["location"] = location_match.group(2).strip() if location_match else ""

    # Summary/Objective section
    summary_match = re.search(r"(?si)(summary|objective):?\s*(.+?)(?=\n\s*\n|work experience|education)", text)
    data["summary"] = summary_match.group(2).strip() if summary_match else ""

    # Section parsing
    sections = {
        "work": r"(?si)work experience:?(.+?)(?=(education|projects|skills|$))",
        "education": r"(?si)education:?(.+?)(?=(work|projects|skills|$))",
        "projects": r"(?si)(projects|key projects):?(.+?)(?=(work|education|skills|$))"
    }

    for section, pattern in sections.items():
        matches = re.search(pattern, text)
        if matches:
            items = []
            entries = re.split(r"\n\s*\n", matches.group(1).strip())
            for entry in entries:
                parts = re.split(r"\n", entry.strip(), 1)
                if len(parts) > 1:
                    items.append({"title": parts[0], "details": parts[1]})
            data[section] = items

    return {k: v for k, v in data.items() if v}

# Rest of the Flask routes remain similar...

@app.route("/")
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route("/upload", methods=["POST"])
def upload_resume():
    if "resume" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["resume"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(file_path)

    text = extract_text_from_pdf(file_path)
    resume_data = parse_resume(text)

    return jsonify(resume_data)

if __name__ == "__main__":
    app.run(debug=True)
