from flask import Flask, request, jsonify, send_file
import requests
import base64
import json
import io
import os
from flask_cors import CORS
import traceback

app = Flask(__name__)
CORS(app)

# Configuration
ASIM_API_URL = "https://a.asim.sh/sim_apis/image_gen"
DEFAULT_SIM_ID = 282195  # Modèle par défaut pour la génération
EDIT_SIM_ID = 272290     # Modèle avec support du ratio pour l'édition

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({
        "status": "active",
        "message": "Image Generation API is running",
        "endpoints": {
            "generate": "/generate (POST)",
            "edit": "/edit (POST)",
            "ignore_ref": "/ignore_ref (POST)"
        }
    })

@app.route('/generate', methods=['POST'])
def generate_image():
    try:
        data = request.get_json()
        if not data or 'prompt' not in data:
            return jsonify({"error": "Le champ 'prompt' est requis"}), 400

        prompt = data['prompt']
        ratio = data.get('ratio')
        output_format = data.get('format', 'jpg').lower()

        if ratio:
            valid_ratios = ['1:1', '16:9', '9:16', '3:4']
            if ratio not in valid_ratios:
                return jsonify({"error": f"Ratio invalide. Utilisez: {', '.join(valid_ratios)}"}), 400

        valid_formats = ['jpg', 'jpeg', 'png']
        if output_format not in valid_formats:
            return jsonify({"error": f"Format invalide. Utilisez: {', '.join(valid_formats)}"}), 400

        # Check if images array is provided
        if 'images' in data and isinstance(data['images'], list) and len(data['images']) > 0:
            # Use edit mode with images
            images_b64 = data['images']
            
            processed_images = []
            for image_b64 in images_b64:
                try:
                    base64.b64decode(image_b64)
                except:
                    return jsonify({"error": "Image base64 invalide"}), 400
                
                if image_b64.startswith('iVBORw'):
                    image_type = 'png'
                else:
                    image_type = 'jpeg'
                    
                processed_images.append(f"data:image/{image_type};base64,{image_b64}")

            payload = {
                "images": json.dumps(processed_images),
                "prompt": prompt,
                "simId": EDIT_SIM_ID
            }
            
        else:
            # Normal generation without images
            payload = {
                "prompt": prompt,
                "simId": DEFAULT_SIM_ID
            }
            if ratio:
                payload["aspectRatio"] = ratio

        headers = {"Content-Type": "application/json"}
        response = requests.post(ASIM_API_URL, headers=headers, json=payload, timeout=120)

        if response.status_code != 200:
            return jsonify({"error": f"Erreur API: {response.status_code}"}), 500

        result = response.json()
        if 'imageUrl' not in result:
            return jsonify({"error": "Pas d'URL d'image dans la réponse"}), 500

        image_response = requests.get(result['imageUrl'], timeout=60)
        if image_response.status_code != 200:
            return jsonify({"error": "Impossible de télécharger l'image générée"}), 500

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
        return jsonify({"error": "Timeout lors de la génération"}), 408
    except Exception as e:
        print(f"Erreur generate: {traceback.format_exc()}")
        return jsonify({"error": f"Erreur interne: {str(e)}"}), 500

@app.route('/edit', methods=['POST'])
def edit_image():
    try:
        data = request.get_json()
        if not data or 'prompt' not in data:
            return jsonify({"error": "Le champ 'prompt' est requis"}), 400

        # Gestion des images
        images_b64 = []
        if 'image' in data:
            images_b64.append(data['image'])
        elif 'images' in data and isinstance(data['images'], list):
            if len(data['images']) > 5:
                return jsonify({"error": "Maximum 5 images de référence autorisées"}), 400
            images_b64 = data['images']
        else:
            return jsonify({"error": "Le champ 'image' ou 'images' est requis"}), 400

        prompt = data['prompt']
        ratio = data.get('ratio')
        output_format = data.get('format', 'jpg').lower()

        if ratio:
            valid_ratios = ['1:1', '16:9', '9:16', '3:4']
            if ratio not in valid_ratios:
                return jsonify({"error": f"Ratio invalide. Utilisez: {', '.join(valid_ratios)}"}), 400

        valid_formats = ['jpg', 'jpeg', 'png']
        if output_format not in valid_formats:
            return jsonify({"error": f"Format invalide. Utilisez: {', '.join(valid_formats)}"}), 400

        processed_images = []
        for image_b64 in images_b64:
            try:
                base64.b64decode(image_b64)
            except:
                return jsonify({"error": "Image base64 invalide"}), 400
            
            if image_b64.startswith('iVBORw'):
                image_type = 'png'
            else:
                image_type = 'jpeg'
                
            processed_images.append(f"data:image/{image_type};base64,{image_b64}")

        payload = {
            "images": json.dumps(processed_images),
            "prompt": prompt,
            "simId": EDIT_SIM_ID
        }
        
        if ratio:
            payload["aspectRatio"] = ratio

        headers = {"Content-Type": "application/json"}
        response = requests.post(ASIM_API_URL, headers=headers, json=payload, timeout=120)

        if response.status_code != 200:
            return jsonify({"error": f"Erreur API: {response.status_code}"}), 500

        result = response.json()
        if 'imageUrl' not in result:
            return jsonify({"error": "Pas d'URL d'image dans la réponse"}), 500

        image_response = requests.get(result['imageUrl'], timeout=60)
        if image_response.status_code != 200:
            return jsonify({"error": "Impossible de télécharger l'image éditée"}), 500

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
        return jsonify({"error": "Timeout lors de l'édition"}), 408
    except Exception as e:
        print(f"Erreur edit: {traceback.format_exc()}")
        return jsonify({"error": f"Erreur interne: {str(e)}"}), 500

@app.route('/ignore_ref', methods=['POST'])
def ignore_ref():
    try:
        data = request.get_json()
        if not data or 'prompt' not in data:
            return jsonify({"error": "Le champ 'prompt' est requis"}), 400

        # Image de référence fixe
        ref_image_url = "https://i.postimg.cc/zGTTCyyM/730ed7b95b581e2d475b7500cac3487a.jpg"
        
        img_resp = requests.get(ref_image_url, timeout=60)
        if img_resp.status_code != 200:
            return jsonify({"error": "Impossible de télécharger l'image de référence"}), 500
        
        img_b64 = base64.b64encode(img_resp.content).decode('utf-8')
        img_type = "png" if ref_image_url.lower().endswith(".png") else "jpeg"
        img_b64_full = f"data:image/{img_type};base64,{img_b64}"

        prompt = (
            "Ignore the reference image you see and create a brand new image from scratch based solely on this new prompt: "
            + data['prompt']
        )

        ratio = data.get('ratio')
        output_format = data.get('format', 'jpg').lower()

        valid_formats = ['jpg', 'jpeg', 'png']
        if output_format not in valid_formats:
            return jsonify({"error": f"Format invalide. Utilisez: {', '.join(valid_formats)}"}), 400

        payload = {
            "images": json.dumps([img_b64_full]),
            "prompt": prompt,
            "simId": EDIT_SIM_ID
        }
        if ratio:
            valid_ratios = ['1:1', '16:9', '9:16', '3:4']
            if ratio not in valid_ratios:
                return jsonify({"error": f"Ratio invalide. Utilisez: {', '.join(valid_ratios)}"}), 400
            payload["aspectRatio"] = ratio

        headers = {"Content-Type": "application/json"}
        response = requests.post(ASIM_API_URL, headers=headers, json=payload, timeout=120)

        if response.status_code != 200:
            return jsonify({"error": f"Erreur API: {response.status_code}"}), 500
        
        result = response.json()
        if 'imageUrl' not in result:
            return jsonify({"error": "Pas d'URL d'image dans la réponse"}), 500

        image_response = requests.get(result['imageUrl'], timeout=60)
        if image_response.status_code != 200:
            return jsonify({"error": "Impossible de télécharger l'image générée"}), 500

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
        return jsonify({"error": "Timeout lors de la génération"}), 408
    except Exception as e:
        print(f"Erreur ignore_ref: {traceback.format_exc()}")
        return jsonify({"error": f"Erreur interne: {str(e)}"}), 500

@app.errorhandler(413)
def too_large(e):
    return jsonify({"error": "Fichier trop volumineux"}), 413

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint non trouvé"}), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({"error": "Erreur serveur interne"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Démarrage sur le port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)


