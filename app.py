from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import fitz  # PyMuPDF (for PDF text extraction)
import re
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# HTML Template with improved UI
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Resume Parser</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f7fa;
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
        }
        h1 {
            color: #2c3e50;
            text-align: center;
            margin-bottom: 30px;
        }
        h2 {
            color: #3498db;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 10px;
            margin-top: 30px;
        }
        .upload-section {
            background: #ecf0f1;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
            text-align: center;
        }
        input[type="file"] {
            background: white;
            padding: 10px;
            border-radius: 4px;
            border: 1px solid #bdc3c7;
            width: 100%;
            max-width: 300px;
        }
        input[type="text"], input[type="email"], textarea {
            width: 100%;
            padding: 12px;
            margin: 8px 0;
            display: inline-block;
            border: 1px solid #ccc;
            border-radius: 4px;
            box-sizing: border-box;
        }
        textarea {
            height: 100px;
            resize: vertical;
        }
        .form-group {
            margin-bottom: 15px;
        }
        button {
            background-color: #3498db;
            color: white;
            padding: 12px 20px;
            margin: 8px 0;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
            transition: background-color 0.3s;
        }
        button:hover {
            background-color: #2980b9;
        }
        .output-section {
            margin-top: 30px;
            background: #f9f9f9;
            padding: 20px;
            border-radius: 8px;
        }
        .section-container {
            margin-bottom: 20px;
        }
        .section-title {
            font-weight: bold;
            margin-bottom: 10px;
            color: #2c3e50;
        }
        .entries-container {
            margin-left: 20px;
        }
        .entry {
            background: #ecf0f1;
            padding: 10px;
            margin-bottom: 10px;
            border-radius: 4px;
            position: relative;
        }
        .remove-btn {
            position: absolute;
            right: 10px;
            top: 10px;
            background: #e74c3c;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 2px 8px;
            cursor: pointer;
        }
        .remove-btn:hover {
            background: #c0392b;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Resume Parser</h1>

        <div class="upload-section">
            <h2>Import from Resume</h2>
            <form id="upload-form" enctype="multipart/form-data">
                <input type="file" id="resume" accept="application/pdf" required>
                <button type="submit">Parse Resume</button>
            </form>
        </div>
        
        <h2>Or Fill Manually</h2>
        <form id="manual-form">
            <div class="form-group">
                <label for="name">Full Name</label>
                <input type="text" id="name" placeholder="John Doe">
            </div>
            
            <div class="form-group">
                <label for="email">Email</label>
                <input type="email" id="email" placeholder="john@example.com">
            </div>
            
            <div class="form-group">
                <label for="phone">Phone Number</label>
                <input type="text" id="phone" placeholder="+91 9876543210">
            </div>
            
            <div class="form-group">
                <label for="experience">Total Experience (Years)</label>
                <input type="text" id="experience" placeholder="5 years">
            </div>
            
            <div class="form-group">
                <label for="linkedin">LinkedIn</label>
                <input type="text" id="linkedin" placeholder="https://linkedin.com/in/johndoe">
            </div>
            
            <div class="form-group">
                <label for="github">GitHub</label>
                <input type="text" id="github" placeholder="https://github.com/johndoe">
            </div>
            
            <div class="form-group">
                <label for="location">Location</label>
                <input type="text" id="location" placeholder="Mumbai, Maharashtra">
            </div>
            
            <div class="form-group">
                <label for="summary">Summary/Objective</label>
                <textarea id="summary" placeholder="A brief summary of your professional background and goals..."></textarea>
            </div>
            
            <div class="section-container" id="work-section">
                <div class="section-title">Work Experience</div>
                <div class="entries-container" id="work-entries"></div>
                <button type="button" onclick="addWorkExperience()">Add Work Experience</button>
            </div>
            
            <div class="section-container" id="education-section">
                <div class="section-title">Education</div>
                <div class="entries-container" id="education-entries"></div>
                <button type="button" onclick="addEducation()">Add Education</button>
            </div>
            
            <div class="section-container" id="skills-section">
                <div class="section-title">Skills</div>
                <div class="entries-container" id="skills-entries"></div>
                <button type="button" onclick="addSkill()">Add Skill</button>
            </div>
            
            <div class="section-container" id="projects-section">
                <div class="section-title">Projects</div>
                <div class="entries-container" id="projects-entries"></div>
                <button type="button" onclick="addProject()">Add Project</button>
            </div>
            
            <div class="section-container" id="certifications-section">
                <div class="section-title">Certifications</div>
                <div class="entries-container" id="certifications-entries"></div>
                <button type="button" onclick="addCertification()">Add Certification</button>
            </div>
            
            <div class="section-container" id="extracurriculars-section">
                <div class="section-title">Extracurricular Activities</div>
                <div class="entries-container" id="extracurriculars-entries"></div>
                <button type="button" onclick="addExtracurricular()">Add Extracurricular</button>
            </div>
            
            <button type="submit">Save Changes</button>
        </form>

        <div id="output" class="output-section"></div>
    </div>
    
    <script>
        // Store all the parsed data
        let resumeData = {
            work: [],
            education: [],
            skills: [],
            projects: [],
            certifications: [],
            extracurriculars: []
        };
        
        // Upload form handler
        document.getElementById('upload-form').addEventListener('submit', async function(event) {
            event.preventDefault();
            const fileInput = document.getElementById('resume');
            const formData = new FormData();
            formData.append('resume', fileInput.files[0]);

            try {
                const response = await fetch('/upload', { method: 'POST', body: formData });
                if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);

                const data = await response.json();
                fillForm(data);
            } catch (error) {
                console.error("Error:", error);
                document.getElementById('output').innerHTML = `<p style="color:red;">Failed to process the resume. Try again.</p>`;
            }
        });

        // Fill the form with parsed data
        function fillForm(data) {
            document.getElementById('name').value = data["Full Name"] || "";
            document.getElementById('email').value = data["Email"] || "";
            document.getElementById('linkedin').value = data["LinkedIn"] || "";
            document.getElementById('phone').value = data["Phone Number"] || "";
            document.getElementById('github').value = data["GitHub"] || "";
            document.getElementById('location').value = data["Location"] || "";
            document.getElementById('summary').value = data["Summary"] || "";
            document.getElementById('experience').value = data["Total Experience"] || "";
            
            // Clear existing entries
            clearEntries();
            
            // Fill work experience
            if (data["Work Experience"] && Array.isArray(data["Work Experience"])) {
                resumeData.work = data["Work Experience"];
                refreshEntries('work');
            }
            
            // Fill education
            if (data["Education"] && Array.isArray(data["Education"])) {
                resumeData.education = data["Education"];
                refreshEntries('education');
            }
            
            // Fill skills
            if (data["Skills"] && Array.isArray(data["Skills"])) {
                resumeData.skills = data["Skills"];
                refreshEntries('skills');
            }
            
            // Fill projects
            if (data["Projects"] && Array.isArray(data["Projects"])) {
                resumeData.projects = data["Projects"];
                refreshEntries('projects');
            }
            
            // Fill certifications
            if (data["Certifications"] && Array.isArray(data["Certifications"])) {
                resumeData.certifications = data["Certifications"];
                refreshEntries('certifications');
            }
            
            // Fill extracurriculars
            if (data["Extracurriculars"] && Array.isArray(data["Extracurriculars"])) {
                resumeData.extracurriculars = data["Extracurriculars"];
                refreshEntries('extracurriculars');
            }
        }
        
        function clearEntries() {
            document.getElementById('work-entries').innerHTML = '';
            document.getElementById('education-entries').innerHTML = '';
            document.getElementById('skills-entries').innerHTML = '';
            document.getElementById('projects-entries').innerHTML = '';
            document.getElementById('certifications-entries').innerHTML = '';
            document.getElementById('extracurriculars-entries').innerHTML = '';
            
            resumeData = {
                work: [],
                education: [],
                skills: [],
                projects: [],
                certifications: [],
                extracurriculars: []
            };
        }
        
        function refreshEntries(type) {
            const container = document.getElementById(`${type}-entries`);
            container.innerHTML = '';
            
            resumeData[type].forEach((item, index) => {
                const entry = document.createElement('div');
                entry.className = 'entry';
                entry.innerHTML = `
                    ${item}
                    <button class="remove-btn" onclick="removeEntry('${type}', ${index})">×</button>
                `;
                container.appendChild(entry);
            });
        }
        
        function removeEntry(type, index) {
            resumeData[type].splice(index, 1);
            refreshEntries(type);
        }
        
        function addWorkExperience() {
            const experience = prompt("Enter work experience (e.g. Company, Position, Duration, Responsibilities):");
            if (experience) {
                resumeData.work.push(experience);
                refreshEntries('work');
            }
        }
        
        function addEducation() {
            const education = prompt("Enter education details (e.g. Degree, Institution, Year, GPA):");
            if (education) {
                resumeData.education.push(education);
                refreshEntries('education');
            }
        }
        
        function addSkill() {
            const skill = prompt("Enter a skill:");
            if (skill) {
                resumeData.skills.push(skill);
                refreshEntries('skills');
            }
        }
        
        function addProject() {
            const project = prompt("Enter project details (e.g. Name, Description, Technologies used):");
            if (project) {
                resumeData.projects.push(project);
                refreshEntries('projects');
            }
        }
        
        function addCertification() {
            const certification = prompt("Enter certification details (e.g. Name, Issuing Organization, Date):");
            if (certification) {
                resumeData.certifications.push(certification);
                refreshEntries('certifications');
            }
        }
        
        function addExtracurricular() {
            const activity = prompt("Enter extracurricular activity:");
            if (activity) {
                resumeData.extracurriculars.push(activity);
                refreshEntries('extracurriculars');
            }
        }
        
        // Manual form submission
        document.getElementById('manual-form').addEventListener('submit', function(event) {
            event.preventDefault();
            
            const outputData = {
                "Full Name": document.getElementById('name').value,
                "Email": document.getElementById('email').value,
                "Phone Number": document.getElementById('phone').value,
                "Total Experience": document.getElementById('experience').value,
                "LinkedIn": document.getElementById('linkedin').value,
                "GitHub": document.getElementById('github').value,
                "Location": document.getElementById('location').value,
                "Summary": document.getElementById('summary').value,
                "Work Experience": resumeData.work,
                "Education": resumeData.education,
                "Skills": resumeData.skills,
                "Projects": resumeData.projects,
                "Certifications": resumeData.certifications,
                "Extracurriculars": resumeData.extracurriculars
            };
            
            document.getElementById('output').innerHTML = `
                <h3>Saved Resume Data:</h3>
                <pre>${JSON.stringify(outputData, null, 2)}</pre>
            `;
        });
    </script>
</body>
</html>
"""

# Function to extract text from PDF
def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = "\n".join([page.get_text("text") for page in doc])
    return text

# Improved function to parse resume
def parse_resume(text):
    data = {}

    # Extract name (look for name at the beginning of the resume)
    name_match = re.search(r"^([A-Z][a-z]+(?:\s[A-Z][a-z]+)+)", text.strip(), re.MULTILINE)
    if name_match:
        data["Full Name"] = name_match.group().strip()
    
    # Extract email
    email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    if email_match:
        data["Email"] = email_match.group().strip()
    
    # Extract LinkedIn URL
    linkedin_match = re.search(r"(https?://)?(www\.)?linkedin\.com/in/[a-zA-Z0-9-_]+", text)
    if linkedin_match:
        data["LinkedIn"] = linkedin_match.group().strip()
    
    # Extract GitHub URL
    github_match = re.search(r"(https?://)?(www\.)?github\.com/[a-zA-Z0-9-_]+", text)
    if github_match:
        data["GitHub"] = github_match.group().strip()
    
    # Extract Indian phone number (with or without +91)
    phone_patterns = [
        r"\+91[\s-]?\d{10}",  # +91 followed by 10 digits
        r"\+91[\s-]?\d{5}[\s-]?\d{5}",  # +91 followed by 5+5 digits pattern
        r"\b\d{10}\b",  # Just 10 digits
        r"\b\d{5}[\s-]?\d{5}\b"  # 5+5 digits pattern
    ]
    
    for pattern in phone_patterns:
        phone_match = re.search(pattern, text)
        if phone_match:
            phone_num = phone_match.group().strip()
            # Clean and format phone number
            phone_num = re.sub(r'[\s-]', '', phone_num)  # Remove spaces and hyphens
            if not phone_num.startswith('+91'):
                phone_num = '+91' + phone_num[-10:]  # Add +91 if missing and keep last 10 digits
            data["Phone Number"] = phone_num
            break
    
    # Extract location (city, state format only)
    location_patterns = [
        r"(?i)(?:^|\n)(?:location|address|city|residence):?\s*([A-Za-z]+[\s,]+[A-Za-z]+)(?=\n|$)",  # Labeled location
        r"(?i)\b([A-Z][a-z]+(?:[\s,]+[A-Z][a-z]+)?(?:[\s,]+[A-Z]{2})?)(?=\n|\s\d|\s\(|$)",  # City, State or City, State Abbreviation
    ]
    
    for pattern in location_patterns:
        location_match = re.search(pattern, text)
        if location_match:
            location = location_match.group(1) if len(location_match.groups()) > 0 else location_match.group()
            # Clean up and standardize format
            location = re.sub(r'(?i)(location|address|city|residence):\s*', '', location)
            location = location.strip()
            # Only keep if it looks like "City, State" or just "City"
            if re.match(r"^[A-Za-z]+(?:[\s,]+[A-Za-z]+)?$", location):
                data["Location"] = location
                break
    
    # Extract total years of experience
    exp_patterns = [
        r"(?i)(?:^|\n)(?:total|overall)?\s*experience:?\s*(\d+(?:\.\d+)?)\s*(?:years|yrs)",  # Labeled experience
        r"(?i)(?:^|\n)(?:with|having)\s+(\d+(?:\.\d+)?)\s*(?:years|yrs).*?experience",  # With X years experience
        r"(?i)(?:^|\n)(\d+(?:\.\d+)?)\s*(?:years|yrs).*?(?:of|in)\s+.*?experience"  # X years of experience
    ]
    
    for pattern in exp_patterns:
        exp_match = re.search(pattern, text)
        if exp_match:
            years = exp_match.group(1).strip()
            data["Total Experience"] = f"{years} years"
            break
    
    # Extract summary/objective
    summary_patterns = [
        r"(?i)(Summary|Profile|Objective|About Me):?\s*(.+?)(?=\n\n|\n[A-Z][A-Z\s]+\n|Work Experience|Education|Skills|$)",
        r"(?i)(Professional Summary|Career Objective):?\s*(.+?)(?=\n\n|\n[A-Z][A-Z\s]+\n|Work Experience|Education|Skills|$)",
    ]
    
    for pattern in summary_patterns:
        summary_match = re.search(pattern, text, re.DOTALL)
        if summary_match:
            summary_text = summary_match.group(2).strip() if len(summary_match.groups()) > 1 else summary_match.group(1).strip()
            data["Summary"] = re.sub(r"\n+", " ", summary_text)
            break
    
    # Extract work experience
    work_exp_section = re.search(r"(?i)(Work Experience|Professional Experience|Employment History)[\s\S]+?(Education|Skills|Projects|$)", text)
    if work_exp_section:
        work_text = work_exp_section.group()
        work_entries = re.findall(r"(?i)(?:^|\n)([A-Z][A-Za-z\s&]+)[\s\n]+((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)[\s\d,]+ - (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December|Present)[\s\d,]+)[\s\n]+([^\n]+)(?:[\s\n]+(.+?))?(?=\n\n[A-Z]|\n[A-Z][A-Za-z\s&]+\n|$)", work_text, re.DOTALL)
        if work_entries:
            data["Work Experience"] = []
            for entry in work_entries:
                company = entry[0].strip()
                duration = entry[1].strip()
                position = entry[2].strip()
                description = entry[3].strip() if len(entry) > 3 and entry[3] else ""
                data["Work Experience"].append(f"{position} at {company}, {duration}\n{description}")
    
    # Extract education
    education_section = re.search(r"(?i)(Education|Academic Background)[\s\S]+?(Skills|Work Experience|Projects|Certifications|$)", text)
    if education_section:
        edu_text = education_section.group()
        edu_entries = re.findall(r"(?i)(?:^|\n)([A-Z][A-Za-z\s&]+)[\s\n]+((?:Bachelor|Master|PhD|BSc|MSc|MBA|Diploma|Certificate|Associate)[\s\S]+?)(?=\n\n[A-Z]|\n[A-Z][A-Za-z\s&]+\n|$)", edu_text)
        if edu_entries:
            data["Education"] = []
            for entry in edu_entries:
                institution = entry[0].strip()
                details = entry[1].strip()
                data["Education"].append(f"{institution}: {details}")
    
    # Extract skills
    skills_section = re.search(r"(?i)(Skills|Technical Skills|Core Competencies|Expertise)[\s\S]+?(Projects|Work Experience|Education|Certifications|$)", text)
    if skills_section:
        skills_text = skills_section.group()
        # Try to find skills as a list
        skills_list = re.findall(r"(?i)(?:^|\n)(?:•|\*|\-|\d+\.)\s*([^•\*\-\n]+)(?=\n|$)", skills_text)
        if skills_list:
            data["Skills"] = [skill.strip() for skill in skills_list]
        else:
            # Try to find comma-separated skills
            skills_comma = re.search(r"(?i):(.*?)(?=\n\n|$)", skills_text)
            if skills_comma:
                skills_str = skills_comma.group(1).strip()
                data["Skills"] = [skill.strip() for skill in skills_str.split(',')]
    
    # Extract projects
    projects_section = re.search(r"(?i)(Projects|Personal Projects|Key Projects)[\s\S]+?(Work Experience|Education|Skills|Certifications|$)", text)
    if projects_section:
        projects_text = projects_section.group()
        project_entries = re.findall(r"(?i)(?:^|\n)([A-Z][A-Za-z\s&\-]+)[\s\n]+(.+?)(?=\n\n[A-Z]|\n[A-Z][A-Za-z\s&\-]+\n|$)", projects_text, re.DOTALL)
        if project_entries:
            data["Projects"] = []
            for entry in project_entries:
                project_name = entry[0].strip()
                project_details = entry[1].strip()
                data["Projects"].append(f"{project_name}: {project_details}")
    
    # Extract certifications
    cert_section = re.search(r"(?i)(Certifications|Professional Certifications|Licenses)[\s\S]+?(Projects|Work Experience|Education|Skills|$)", text)
    if cert_section:
        cert_text = cert_section.group()
        cert_entries = re.findall(r"(?i)(?:^|\n)(?:•|\*|\-|\d+\.)\s*([^•\*\-\n]+)(?=\n|$)", cert_text)
        if cert_entries:
            data["Certifications"] = [cert.strip() for cert in cert_entries]
    
    # Extract extracurricular activities
    extra_section = re.search(r"(?i)(Extracurricular Activities|Leadership|Volunteer Work|Additional Activities)[\s\S]+?(Projects|Work Experience|Education|Skills|Certifications|$)", text)
    if extra_section:
        extra_text = extra_section.group()
        extra_entries = re.findall(r"(?i)(?:^|\n)(?:•|\*|\-|\d+\.)\s*([^•\*\-\n]+)(?=\n|$)", extra_text)
        if extra_entries:
            data["Extracurriculars"] = [extra.strip() for extra in extra_entries]
    
    return {k: v for k, v in data.items() if v}

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