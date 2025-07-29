from flask import Flask, request, render_template_string
import os
import fitz  # PyMuPDF
from werkzeug.utils import secure_filename
import shutil
import time

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
        code {
            color: green;
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

        # Save uploaded file
        if file and file.filename.endswith(".pdf"):
            filename = secure_filename(file.filename)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            file.save(file_path)

            # Create output directory
            os.makedirs(output_path, exist_ok=True)

            try:
                split_pdf_chapters(file_path, output_path)
                result = f"Chapters split successfully and saved to: <code>{output_path}</code> (ZIP also available)"
            except Exception as e:
                result = f"❌ Error: {str(e)}"
        else:
            result = "❌ Invalid file. Please upload a PDF."

    return render_template_string(TEMPLATE, result=result)

def split_pdf_chapters(pdf_path, output_dir):
    start_time = time.time()
    doc = fitz.open(pdf_path)
    chapters = {}

    for i, page in enumerate(doc):
        text = page.get_text("text")
        lines = text.splitlines()

        for line in lines:
            if line.strip().lower().startswith("chapter"):
                chapter_title = line.strip()
                if chapter_title not in chapters:
                    chapters[chapter_title] = i
                    break

    if not chapters:
        raise Exception("No chapters found in the PDF.")

    chapter_items = sorted(chapters.items(), key=lambda x: x[1])

    for idx, (title, start_page) in enumerate(chapter_items):
        end_page = chapter_items[idx + 1][1] if idx + 1 < len(chapter_items) else len(doc)
        safe_title = title.replace(":", " -").replace("/", "-").replace("\\", "-").strip()
        output_pdf_path = os.path.join(output_dir, f"{safe_title}.pdf")

        chapter_doc = fitz.open()
        chapter_doc.insert_pdf(doc, from_page=start_page, to_page=end_page - 1)
        chapter_doc.save(output_pdf_path)
        chapter_doc.close()

    shutil.make_archive(output_dir, 'zip', output_dir)
    print(f"✅ PDF split completed in {time.time() - start_time:.2f} seconds.")

if __name__ == "__main__":
    app.run(debug=True)
