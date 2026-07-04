import os
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from google import genai
from google.genai import types

app = FastAPI()

# Force global security clearance for your local files
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Safely pull your secret key from the cloud environment instead of exposing it in code
API_KEY = os.environ.get("GEMINI_API_KEY") 
client = genai.Client(api_key=API_KEY)

# Your backend will serve the frontend page directly
@app.get("/", response_class=HTMLResponse)
async def read_index():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Scorpio Rizn - AI Scanner</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                background-color: #0d1117;
                color: #c9d1d9;
                margin: 0;
                padding: 20px;
                display: flex;
                flex-direction: column;
                align-items: center;
            }
            .container {
                max-width: 500px;
                width: 100%;
                background-color: #161b22;
                padding: 25px;
                border-radius: 12px;
                border: 1px solid #30363d;
                box-shadow: 0 8px 24px rgba(0,0,0,0.5);
            }
            h1 { color: #f0f6fc; text-align: center; font-size: 24px; margin-bottom: 20px; }
            .input-group { margin-bottom: 15px; }
            label { display: block; margin-bottom: 8px; font-weight: 600; font-size: 14px; }
            input[type="file"] {
                width: 100%;
                padding: 10px;
                background: #21262d;
                border: 1px dashed #8b949e;
                border-radius: 6px;
                color: #c9d1d9;
                box-sizing: border-box;
                cursor: pointer;
            }
            button {
                width: 100%;
                background-color: #238636;
                color: white;
                border: none;
                padding: 12px;
                font-size: 16px;
                font-weight: bold;
                border-radius: 6px;
                cursor: pointer;
                margin-top: 10px;
            }
            button:disabled { background-color: #21262d; color: #8b949e; cursor: not-allowed; }
            #loading { display: none; text-align: center; margin-top: 15px; font-style: italic; color: #58a6ff; }
            #resultContainer { margin-top: 25px; display: none; }
            h2 { color: #58a6ff; font-size: 18px; margin-bottom: 10px; }
            pre {
                background-color: #0d1117;
                padding: 15px;
                border-radius: 6px;
                border: 1px solid #30363d;
                white-space: pre-wrap;
                word-wrap: break-word;
                line-height: 1.5;
            }
        </style>
    </head>
    <body>
    <div class="container">
        <h1>Scorpio Rizn AI Reseller</h1>
        <div class="input-group">
            <label>📸 Photo 1: Full Item (with Quarter coin)</label>
            <input type="file" id="shirtInput" accept="image/*">
        </div>
        <div class="input-group">
            <label>🏷️ Photo 2: Care / Wash / Size Tag</label>
            <input type="file" id="tagInput" accept="image/*">
        </div>
        <button id="scanBtn" onclick="runAIScan()">Generate Marketplace Listing</button>
        <div id="loading">🧠 Processing images and scaling sizes via AI... Please wait...</div>
        <div id="resultContainer">
            <h2>✨ AI Generated Output:</h2>
            <pre id="resultText"></pre>
        </div>
    </div>

    <script>
    async function runAIScan() {
        const shirtInput = document.getElementById('shirtInput');
        const tagInput = document.getElementById('tagInput');

        if (shirtInput.files.length === 0 || tagInput.files.length === 0) {
            alert("Please upload both photos to continue!");
            return;
        }

        const btn = document.getElementById('scanBtn');
        const loading = document.getElementById('loading');
        const resultContainer = document.getElementById('resultContainer');
        const resultText = document.getElementById('resultText');

        btn.disabled = true;
        loading.style.display = "block";
        resultContainer.style.display = "none";

        const formData = new FormData();
        formData.append("shirt", shirtInput.files[0]);
        formData.append("tag", tagInput.files[0]);

        try {
            const response = await fetch("/scan-clothing/", {
                method: "POST",
                body: formData
            });
            const data = await response.json();
            if (data.success) {
                resultText.innerText = data.listing;
                resultContainer.style.display = "block";
            } else {
                alert("API Error: " + data.error);
            }
        } catch (err) {
            alert("Connection error occurred.");
            console.error(err);
        } finally {
            btn.disabled = false;
            loading.style.display = "none";
        }
    }
    </script>
    </body>
    </html>
    """

@app.post("/scan-clothing/")
async def scan_clothing(shirt: UploadFile = File(...), tag: UploadFile = File(...)):
    try:
        shirt_bytes = await shirt.read()
        tag_bytes = await tag.read()

        image_shirt = types.Part.from_bytes(data=shirt_bytes, mime_type="image/jpeg")
        image_tag = types.Part.from_bytes(data=tag_bytes, mime_type="image/jpeg")

        # Perfectly formatted universal prompt
        prompt = (
            "You are an expert reselling assistant for eBay and Vinted. "
            "Analyze these two images. One image contains the full retail item (clothing, shoes, or accessory) "
            "along with a standard US Quarter coin (0.955 inches in diameter) placed on it as a size reference. "
            "First, locate the quarter. Use its known size to visually calculate the approximate real-world measurements "
            "relevant to this specific item type (e.g., pit-to-pit/length for tops, waist/inseam for pants, outsole for shoes).\n\n"
            "Next, read the care tag/branding for materials and sizing. Finally, generate an optimized marketplace listing. "
            "Do NOT use placeholders like [Insert Measurement Here]. Fill in the exact measurements you calculated."
        )

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[image_shirt, image_tag, prompt]
        )
        return {"success": True, "listing": response.text}
    except Exception as e:
        return {"success": False, "error": str(e)}
