from flask import Flask, request, render_template_string
import os
import fitz  # PyMuPDF
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>PDF Chapter Splitter</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            background: #f8f9fa;
        }
        .container {
            max-width: 600px;
            margin-top: 80px;
            background: white;
            padding: 40px;
            border-radius: 15px;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
        }
        .form-label {
            font-weight: 500;
        }
        .btn-primary {
            width: 100%;
        }
        .result {
            margin-top: 20px;
        }
    </style>
</head>
<body>
<div class="container">
    <h2 class="text-center mb-4">📘 PDF Chapter Splitter</h2>
    <form method="POST" enctype="multipart/form-data">
        <div class="mb-3">
            <label class="form-label">Select PDF File:</label>
            <input class="form-control" type="file" name="file" required>
        </div>
        <div class="mb-3">
            <label class="form-label">Output Folder Name:</label>
            <input class="form-control" type="text" name="output_path" value="output_chapters_pdf" required>
        </div>
        <button type="submit" class="btn btn-primary">📂 Split Chapters</button>
    </form>

    {% if result %}
    <div class="alert alert-success result" role="alert">
        ✅ {{ result }}
    </div>
    {% endif %}
</div>
</body>
</html>
'''

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    if request.method == "POST":
        file = request.files["file"]
        output_path = request.form["output_path"].strip()
        os.makedirs(output_path, exist_ok=True)

        if file and file.filename.endswith(".pdf"):
            filename = secure_filename(file.filename)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)

            split_pdf_chapters(file_path, output_path)
            result = f"Chapters split successfully and saved to: <code>{output_path}</code>"
        else:
            result = "❌ Invalid file. Please upload a PDF."

    return render_template_string(TEMPLATE, result=result)

def split_pdf_chapters(pdf_path, output_dir):
    doc = fitz.open(pdf_path)
    chapters = {}

    for i, page in enumerate(doc):
        text = page.get_text()
        if "Chapter " in text:
            for line in text.splitlines():
                if line.strip().startswith("Chapter"):
                    chapter_title = line.strip()
                    chapters[chapter_title] = i
                    break

    chapter_items = sorted(chapters.items(), key=lambda x: x[1])

    for idx, (title, start_page) in enumerate(chapter_items):
        end_page = chapter_items[idx + 1][1] if idx + 1 < len(chapter_items) else len(doc)
        safe_title = title.replace(":", " -").replace("/", "-").strip()
        output_pdf_path = os.path.join(output_dir, f"{safe_title}.pdf")

        chapter_doc = fitz.open()
        for page_num in range(start_page, end_page):
            chapter_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)

        chapter_doc.save(output_pdf_path)
        chapter_doc.close()

if __name__ == "__main__":
    app.run(debug=True)
