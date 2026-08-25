# API de Génération d'Images

Cette API permet de générer et éditer des images en utilisant l'IA.

## 🚀 Déploiement

L'API est prête pour être déployée sur Render.com

## 📋 Endpoints

### 1. Health Check
```
GET /
```
Retourne le statut de l'API et la liste des endpoints disponibles.

### 2. Génération d'image (sans référence)
```
POST /generate
Content-Type: application/json

{
    "prompt": "Description de l'image à générer",
    "ratio": "9:16" | "16:9" | "1:1" (optionnel, défaut: "9:16"),
    "format": "jpg" | "png" (optionnel, défaut: "jpg")
}
```

**Ratios disponibles :**
- `9:16` - Portrait (défaut)
- `16:9` - Paysage  
- `1:1` - Carré

### 3. Édition d'image (avec référence base64)
```
POST /edit
Content-Type: application/json

{
    "image": "base64_string_brut_sans_prefixe",
    "prompt": "Description de l'édition à effectuer",
    "format": "jpg" | "png" (optionnel, défaut: "jpg")
}
```

⚠️ **Important :** Le champ `image` doit contenir uniquement le base64 brut, sans le préfixe `data:image/...`

## 📤 Réponses

- **Succès (200)**: L'image générée/éditée est retournée directement en binaire
- **Erreur (4xx/5xx)**: JSON avec le champ `{"error": "message d'erreur"}`

## 🛠️ Exemples d'utilisation

### Génération simple
```bash
curl -X POST "https://votre-api.onrender.com/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A beautiful sunset over mountains",
    "ratio": "16:9",
    "format": "jpg"
  }' \
  --output generated_image.jpg
```

### Édition avec référence
```bash
# Convertir l'image en base64 brut
IMAGE_B64=$(base64 -w 0 -i mon_image.jpg)

curl -X POST "https://votre-api.onrender.com/edit" \
  -H "Content-Type: application/json" \
  -d "{
    \"image\": \"$IMAGE_B64\",
    \"prompt\": \"Make this image more realistic with better lighting\",
    \"format\": \"png\"
  }" \
  --output edited_image.png
```

### Test depuis JavaScript
```javascript
// Génération
const generateImage = async () => {
  const response = await fetch('https://votre-api.onrender.com/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      prompt: 'A futuristic city at night',
      ratio: '16:9',
      format: 'jpg'
    })
  });
  
  if (response.ok) {
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    // Utiliser l'URL pour afficher l'image
  }
};

// Édition avec base64
const editImage = async (imageBase64) => {
  const response = await fetch('https://votre-api.onrender.com/edit', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      image: imageBase64, // base64 brut sans préfixe
      prompt: 'Make it look like a painting',
      format: 'png'
    })
  });
  
  if (response.ok) {
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    // Utiliser l'URL pour afficher l'image éditée
  }
};
```

## 🔧 Installation locale

```bash
# Cloner le repo
git clone https://github.com/votre-username/image-gen-api.git
cd image-gen-api

# Installer les dépendances
pip install -r requirements.txt

# Lancer l'API
python app.py
```

L'API sera disponible sur `http://localhost:5000`

## 🚀 Déploiement sur Render

1. **Créer un repo GitHub** avec tous ces fichiers
2. **Sur Render.com :**
   - New → Web Service
   - Connect your GitHub repo
   - Render détectera automatiquement Python
   - Le déploiement se fera automatiquement

3. **Variables d'environnement (optionnel) :**
   - `PORT` : Port d'écoute (défaut: 5000)

## ⚡ Limites et considérations

- **Timeout :** 60 secondes pour la génération, 30 secondes pour le téléchargement
- **Format base64 :** Pas de limite de taille explicite, mais Render a des limites de requête
- **CORS :** Activé pour toutes les origines
- **Formats supportés :** JPG/JPEG, PNG en entrée et sortie

## 🐛 Gestion d'erreurs

L'API retourne des codes d'erreur appropriés :
- `400` : Paramètres manquants ou invalides
- `408` : Timeout de génération
- `413` : Fichier trop volumineux
- `500` : Erreur interne du serveur

## 📝 Logs

L'API log automatiquement les erreurs pour faciliter le debugging en production.

