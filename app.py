from flask import Flask, request, jsonify, send_file, send_from_directory
import requests
import base64
import json
import io
import os
from flask_cors import CORS
import traceback

app = Flask(__name__)
CORS(app)

ASIM_API_URL = "https://a.asim.sh/sim_apis/image_gen"
DEFAULT_SIM_ID = 282195
EDIT_SIM_ID = 272290

@app.route('/')
def home():
    return send_file('static/docs/index.html')

@app.route('/api')
def api_status():
    return jsonify({
        "status": "active",
        "creator": "raihan07",
        "message": "Image Generation API is running",
        "endpoints": {
            "generate": "/generate (POST)",
            "edit": "/edit (POST)",
            "ignore_ref": "/ignore_ref (POST)"
        }
    })

@app.route('/docs/<path:filename>')
def serve_static(filename):
    return send_from_directory('static/docs', filename)

@app.route('/generate', methods=['POST'])
def generate_image():
    try:
        data = request.get_json()
        if not data or 'prompt' not in data:
            return jsonify({"error": "The 'prompt' field is required"}), 400

        prompt = data['prompt']
        ratio = data.get('ratio', '9:16')
        output_format = data.get('format', 'jpg').lower()

        valid_ratios = ['1:1', '16:9', '9:16', '3:4']
        if ratio not in valid_ratios:
            return jsonify({"error": f"Invalid ratio. Use: {', '.join(valid_ratios)}"}), 400

        valid_formats = ['jpg', 'jpeg', 'png']
        if output_format not in valid_formats:
            return jsonify({"error": f"Invalid format. Use: {', '.join(valid_formats)}"}), 400

        payload = {
            "prompt": prompt,
            "simId": DEFAULT_SIM_ID,
            "aspectRatio": ratio
        }

        if 'images' in data and isinstance(data['images'], list) and len(data['images']) > 0:
            images_b64 = data['images']
            processed_images = []
            for image_b64 in images_b64:
                try:
                    base64.b64decode(image_b64)
                except:
                    return jsonify({"error": "Invalid base64 image"}), 400
                image_type = 'png' if image_b64.startswith('iVBORw') else 'jpeg'
                processed_images.append(f"data:image/{image_type};base64,{image_b64}")
            
            payload = {
                "images": json.dumps(processed_images),
                "prompt": prompt,
                "simId": EDIT_SIM_ID
            }
            if ratio:
                payload["aspectRatio"] = ratio

        print(f"Generate Payload: {payload}")

        headers = {"Content-Type": "application/json"}
        response = requests.post(ASIM_API_URL, headers=headers, json=payload, timeout=120)

        print(f"Generate Response Status: {response.status_code}")
        print(f"Generate Response Body: {response.text}")

        if response.status_code != 200:
            error_msg = response.json().get('error', 'Unknown error') if response.text else 'No error message'
            return jsonify({"error": f"ASIM API error: {error_msg}"}), 500

        result = response.json()
        if 'imageUrl' not in result:
            return jsonify({"error": "No image URL in response"}), 500

        image_response = requests.get(result['imageUrl'], timeout=60)
        if image_response.status_code != 200:
            return jsonify({"error": "Failed to download generated image"}), 500

        mimetype = f"image/{output_format}"
        if output_format == "jpg":
            mimetype = "image/jpeg"

        return send_file(
            io.BytesIO(image_response.content),
            mimetype=mimetype,
            as_attachment=False,
            download_name=f'generated_image.{output_format}'
        )

    except requests.exceptions.Timeout:
        return jsonify({"error": "Generation timeout"}), 408
    except Exception as e:
        print(f"Generate error: {traceback.format_exc()}")
        return jsonify({"error": f"Internal error: {str(e)}"}), 500

@app.route('/edit', methods=['POST'])
def edit_image():
    try:
        data = request.get_json()
        if not data or 'prompt' not in data:
            return jsonify({"error": "The 'prompt' field is required"}), 400

        images_b64 = []
        if 'image' in data:
            images_b64.append(data['image'])
        elif 'images' in data and isinstance(data['images'], list):
            if len(data['images']) > 5:
                return jsonify({"error": "Maximum 5 reference images allowed"}), 400
            images_b64 = data['images']
        else:
            return jsonify({"error": "The 'image' or 'images' field is required"}), 400

        prompt = data['prompt']
        ratio = data.get('ratio', '9:16')
        output_format = data.get('format', 'jpg').lower()

        valid_ratios = ['1:1', '16:9', '9:16', '3:4']
        if ratio not in valid_ratios:
            return jsonify({"error": f"Invalid ratio. Use: {', '.join(valid_ratios)}"}), 400

        valid_formats = ['jpg', 'jpeg', 'png']
        if output_format not in valid_formats:
            return jsonify({"error": f"Invalid format. Use: {', '.join(valid_formats)}"}), 400

        processed_images = []
        for image_b64 in images_b64:
            try:
                base64.b64decode(image_b64)
            except:
                return jsonify({"error": "Invalid base64 image"}), 400
            image_type = 'png' if image_b64.startswith('iVBORw') else 'jpeg'
            processed_images.append(f"data:image/{image_type};base64,{image_b64}")

        payload = {
            "images": json.dumps(processed_images),
            "prompt": prompt,
            "simId": EDIT_SIM_ID
        }
        if ratio:
            payload["aspectRatio"] = ratio

        print(f"Edit Payload: {payload}")

        headers = {"Content-Type": "application/json"}
        response = requests.post(ASIM_API_URL, headers=headers, json=payload, timeout=120)

        print(f"Edit Response Status: {response.status_code}")
        print(f"Edit Response Body: {response.text}")

        if response.status_code != 200:
            error_msg = response.json().get('error', 'Unknown error') if response.text else 'No error message'
            return jsonify({"error": f"ASIM API error: {error_msg}"}), 500

        result = response.json()
        if 'imageUrl' not in result:
            return jsonify({"error": "No image URL in response"}), 500

        image_response = requests.get(result['imageUrl'], timeout=60)
        if image_response.status_code != 200:
            return jsonify({"error": "Failed to download edited image"}), 500

        mimetype = f"image/{output_format}"
        if output_format == "jpg":
            mimetype = "image/jpeg"

        return send_file(
            io.BytesIO(image_response.content),
            mimetype=mimetype,
            as_attachment=False,
            download_name=f'edited_image.{output_format}'
        )

    except requests.exceptions.Timeout:
        return jsonify({"error": "Edit timeout"}), 408
    except Exception as e:
        print(f"Edit error: {traceback.format_exc()}")
        return jsonify({"error": f"Internal error: {str(e)}"}), 500

@app.route('/ignore_ref', methods=['POST'])
def ignore_ref():
    try:
        data = request.get_json()
        if not data or 'prompt' not in data:
            return jsonify({"error": "The 'prompt' field is required"}), 400

        ref_image_url = "https://i.postimg.cc/zGTTCyyM/730ed7b95b581e2d475b7500cac3487a.jpg"
        
        img_resp = requests.get(ref_image_url, timeout=60)
        if img_resp.status_code != 200:
            return jsonify({"error": "Failed to download reference image"}), 500
        
        img_b64 = base64.b64encode(img_resp.content).decode('utf-8')
        img_type = "png" if ref_image_url.lower().endswith(".png") else "jpeg"
        img_b64_full = f"data:image/{img_type};base64,{img_b64}"

        prompt = (
            "Ignore the reference image you see and create a brand new image from scratch based solely on this new prompt: "
            + data['prompt']
        )

        ratio = data.get('ratio', '9:16')
        output_format = data.get('format', 'jpg').lower()

        valid_ratios = ['1:1', '16:9', '9:16', '3:4']
        if ratio not in valid_ratios:
            return jsonify({"error": f"Invalid ratio. Use: {', '.join(valid_ratios)}"}), 400

        valid_formats = ['jpg', 'jpeg', 'png']
        if output_format not in valid_formats:
            return jsonify({"error": f"Invalid format. Use: {', '.join(valid_formats)}"}), 400

        payload = {
            "images": json.dumps([img_b64_full]),
            "prompt": prompt,
            "simId": EDIT_SIM_ID
        }
        if ratio:
            payload["aspectRatio"] = ratio

        print(f"Ignore Ref Payload: {payload}")

        headers = {"Content-Type": "application/json"}
        response = requests.post(ASIM_API_URL, headers=headers, json=payload, timeout=120)

        print(f"Ignore Ref Response Status: {response.status_code}")
        print(f"Ignore Ref Response Body: {response.text}")

        if response.status_code != 200:
            error_msg = response.json().get('error', 'Unknown error') if response.text else 'No error message'
            return jsonify({"error": f"ASIM API error: {error_msg}"}), 500
        
        result = response.json()
        if 'imageUrl' not in result:
            return jsonify({"error": "No image URL in response"}), 500

        image_response = requests.get(result['imageUrl'], timeout=60)
        if image_response.status_code != 200:
            return jsonify({"error": "Failed to download generated image"}), 500

        mimetype = f"image/{output_format}"
        if output_format == "jpg":
            mimetype = "image/jpeg"

        return send_file(
            io.BytesIO(image_response.content),
            mimetype=mimetype,
            as_attachment=False,
            download_name=f'ignore_ref_image.{output_format}'
        )

    except requests.exceptions.Timeout:
        return jsonify({"error": "Generation timeout"}), 408
    except Exception as e:
        print(f"Ignore_ref error: {traceback.format_exc()}")
        return jsonify({"error": f"Internal error: {str(e)}"}), 500

@app.errorhandler(413)
def too_large(e):
    return jsonify({"error": "File too large"}), 413

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
