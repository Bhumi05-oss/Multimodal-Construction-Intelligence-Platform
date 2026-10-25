
import os
import cv2
import numpy as np
from flask import Flask, request, render_template_string
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Basic application configuration
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Construction Intelligence Platform</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #f3f5f8;
            margin: 0;
            color: #222;
        }
        header {
            background: #1f2937;
            color: white;
            padding: 25px;
            text-align: center;
        }
        main {
            max-width: 850px;
            margin: 30px auto;
            padding: 20px;
        }
        .card {
            background: white;
            padding: 25px;
            margin-bottom: 20px;
            border-radius: 12px;
            box-shadow: 0 3px 12px #00000012;
        }
        label {
            display: block;
            margin: 15px 0 8px;
            font-weight: bold;
        }
        input, textarea {
            width: 100%;
            box-sizing: border-box;
            padding: 12px;
            border: 1px solid #ccc;
            border-radius: 6px;
        }
        button {
            margin-top: 20px;
            padding: 12px 22px;
            border: none;
            border-radius: 6px;
            background: #f59e0b;
            color: #111;
            font-weight: bold;
            cursor: pointer;
        }
        button:hover {
            background: #d97706;
        }
        .result {
            line-height: 1.8;
            overflow-wrap: anywhere;
        }
        .error {
            color: #b91c1c;
            background: #fee2e2;
            padding: 12px;
            border-radius: 6px;
        }
        .note {
            color: #555;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <header>
        <h1>Multimodal Construction Intelligence Platform</h1>
        <p>Construction Site Image and Text Analysis</p>
    </header>

    <main>
        <section class="card">
            <h2>Analyze Construction Site</h2>
            <p>Upload a site image and describe your observations.</p>

            {% if error %}
                <p class="error">{{ error }}</p>
            {% endif %}

            <form method="POST" enctype="multipart/form-data">
                <label for="site_image">Construction Site Image</label>
                <input
                    type="file"
                    id="site_image"
                    name="site_image"
                    accept=".png,.jpg,.jpeg,.webp"
                    required
                >

                <label for="description">Site Description</label>
                <textarea
                    id="description"
                    name="description"
                    rows="5"
                    placeholder="Describe the construction site, materials, visible issues, or safety concerns..."
                    required
                ></textarea>

                <button type="submit">Analyze Site</button>
            </form>
        </section>

        {% if report %}
        <section class="card result">
            <h2>Analysis Report</h2>
            <p><strong>Site Description:</strong> {{ report.description }}</p>
            <p><strong>Image Dimensions:</strong> {{ report.dimensions }}</p>
            <p><strong>Average Brightness:</strong> {{ report.brightness }}</p>
            <p><strong>Image Contrast:</strong> {{ report.contrast }}</p>

            <h3>Text-Based Observations</h3>
            {% if report.observations %}
                <ul>
                    {% for observation in report.observations %}
                        <li>{{ observation }}</li>
                    {% endfor %}
                </ul>
            {% else %}
                <p>No configured construction keywords were found in the description.</p>
            {% endif %}

            <p class="note">
                This is a preliminary image-statistics and keyword-based report.
                It does not identify structural defects or certify site safety.
                A qualified construction professional should verify any concerns.
            </p>
        </section>
        {% endif %}
    </main>
</body>
</html>
"""


def allowed_file(filename):
    """Check whether the uploaded file has an allowed extension."""
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def analyze_image(image_path):
    """Calculate basic image statistics using OpenCV."""
    image = cv2.imread(image_path)

    if image is None:
        raise ValueError("The uploaded file could not be read as an image.")

    height, width = image.shape[:2]

    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    brightness = float(np.mean(gray_image))
    contrast = float(np.std(gray_image))

    return {
        "dimensions": f"{width} x {height} pixels",
        "brightness": round(brightness, 2),
        "contrast": round(contrast, 2),
    }


def analyze_description(description):
    """Find configured construction-related keywords in the text."""
    text = description.lower()

    keyword_rules = {
        "crack": "The description mentions a possible crack. Request a professional inspection.",
        "leak": "The description mentions a possible leak. Check the affected area.",
        "helmet": "The description mentions helmets. Verify that appropriate head protection is used.",
        "scaffold": "The description mentions scaffolding. Verify that it is inspected and properly secured.",
        "exposed wire": "The description mentions exposed wiring. Arrange an electrical safety inspection.",
        "debris": "The description mentions debris. Review housekeeping and access routes.",
        "fall": "The description mentions a possible fall hazard. Have a competent person assess the area.",
        "concrete": "Concrete is mentioned in the description. Verify the relevant construction requirements.",
    }

    observations = []

    for keyword, message in keyword_rules.items():
        if keyword in text:
            observations.append(message)

    return observations


@app.route("/", methods=["GET", "POST"])
def home():
    report = None
    error = None

    if request.method == "POST":
        uploaded_file = request.files.get("site_image")
        description = request.form.get("description", "").strip()

        if not uploaded_file or uploaded_file.filename == "":
            error = "Please select a construction site image."

        elif not allowed_file(uploaded_file.filename):
            error = "Please upload a PNG, JPG, JPEG, or WEBP image."

        elif not description:
            error = "Please enter a site description."

        else:
            filename = secure_filename(uploaded_file.filename)

            # Use a unique name to avoid overwriting existing uploads.
            import uuid
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            image_path = os.path.join(
                app.config["UPLOAD_FOLDER"], unique_filename
            )

            try:
                uploaded_file.save(image_path)

                image_data = analyze_image(image_path)
                observations = analyze_description(description)

                report = {
                    "description": description,
                    "dimensions": image_data["dimensions"],
                    "brightness": image_data["brightness"],
                    "contrast": image_data["contrast"],
                    "observations": observations,
                }

            except (ValueError, cv2.error):
                error = "The image could not be processed. Please upload a valid image."

            finally:
                # Remove the temporary uploaded image after processing.
                if os.path.exists(image_path):
                    os.remove(image_path)

    return render_template_string(
        HTML_PAGE,
        report=report,
        error=error
    )


@app.errorhandler(413)
def file_too_large(error):
    return render_template_string(
        HTML_PAGE,
        report=None,
        error="The image is too large. Please upload an image under 10 MB."
    ), 413


if __name__ == "__main__":
    app.run(debug=True)
