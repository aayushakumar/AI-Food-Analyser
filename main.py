from flask import Flask, request, render_template, jsonify
from google.cloud import vision
import os
import requests
from flask_cors import CORS  # Import Flask-CORS

# Initialize Flask app
app = Flask(__name__) 
CORS(app)

allowed_foods = {
    "banana": "banana, raw",
    "orange": "orange, raw",
    "apple": "apple, raw",
    "pineapple": "pineapple, raw",
    'strawberry': 'strawberry, raw',
    'grape': 'grape, raw',
    'lemon': 'lemon, raw',
    'pear': 'pear, raw',
    'plum': 'plum, raw',
    'watermelon': 'watermelon, raw',
    'mango': 'mango, raw',
    'kiwi': 'kiwi, raw',
    'avocado': 'avocado, raw',
    'pomegranate': 'pomegranate, raw',
    'papaya': 'papaya, raw',
    'cherry': 'cherry, raw',
    'cantaloupe': 'cantaloupe, raw',
    'egg': 'eggs, raw',
    'pot pie': 'pot pie, chicken',
    'onion': 'onion, raw',
    'garlic': 'garlic, raw',
}

API_KEY = "FOpphPCvu3G2xLCcJLVGTXhPtiI4rmlAS5HHZ9bO"
BASE_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"


# Set up Google Cloud Vision client
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'cs415-442121-1433631f68e7.json'
vision_client = vision.ImageAnnotatorClient()

#Fetch nutritional information for a food item from USDA FoodData Central
def get_usda_food_macros(food_name):
    params = {
        "query": food_name,
        "pageSize": 1,  # Limit results
        "api_key": API_KEY
    }
    response = requests.get(BASE_URL, params=params)
    if response.status_code == 200:
        data = response.json()
        if "foods" in data and len(data["foods"]) > 0:
            food = data["foods"][0]  # Get the first match
            # Extract macronutrients if available
            print(food)
            macros = {
                "calories": next((f'{nutrient["value"]} {nutrient["unitName"]}' for nutrient in food.get("foodNutrients", []) if
                                  nutrient.get("nutrientName") == "Energy"), "N/A"),
                "protein": next((f'{nutrient["value"]} {nutrient["unitName"]}' for nutrient in food.get("foodNutrients", []) if
                                 nutrient.get("nutrientName") == "Protein"), "N/A"),
                "carbs": next((f'{nutrient["value"]} {nutrient["unitName"]}' for nutrient in food.get("foodNutrients", []) if
                               nutrient.get("nutrientName") == "Carbohydrate, by difference"), "N/A"),
                "fiber": next((f'{nutrient["value"]} {nutrient["unitName"]}' for nutrient in food.get("foodNutrients", []) if
                               nutrient.get("nutrientName") == "Fiber, total dietary"), "N/A"),
            }
            return macros
    return None


#Get recipes using Spoonacular API for a given ingredient
def get_recipes_for_ingredient(ingredient):
    url = f"https://www.themealdb.com/api/json/v1/1/filter.php?i={ingredient}"

    response = requests.get(url)

    recipes =[]

    if response.status_code == 200:
        data = response.json()
        meals = data.get('meals', [])
        if meals is None:
            return recipes
        for meal in meals:
            recipe = {
                'title': meal['strMeal'],
                'url': f"https://www.themealdb.com/meal/{meal['idMeal']}",
                'image': meal['strMealThumb']
            }
            recipes.append(recipe)
    return recipes

@app.route('/')
def index():
    return render_template('index.html')

# Handle food image upload and analysis
@app.route('/analyze', methods=['POST'])
def analyze():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400

    image_file = request.files['image']
    image_content = image_file.read()

    # Perform label detection using Google Vision API
    image = vision.Image(content=image_content)
    response = vision_client.label_detection(image=image)
    labels = response.label_annotations

    # Extract potential food items
    food_items = [label.description for label in labels]
    filtered_food_items = [item for item in food_items if item.lower() in allowed_foods]
    print(food_items)

    if len(filtered_food_items) == 0:
        return jsonify({'message': 'No food items found'}), 200

    usda_food_names = [allowed_foods[item.lower()] for item in filtered_food_items]
    macros = {}

    # print(filtered_food_items)

    for item in usda_food_names:
        info = get_usda_food_macros(item)
        if info:
            macros[item] = info

    recipes = []
    for item in filtered_food_items:
        recipes.extend(get_recipes_for_ingredient(item))

    if len(recipes) == 0:
        return jsonify({
            'detected_foods': filtered_food_items,
            'macros per 100g': macros,
            'recipes': 'no recipes found',
        })

    return jsonify({
        'detected_foods': filtered_food_items,
        'macros per 100g': macros,
        'recipes': recipes,
    })

if __name__ == '__main__':
    app.run(debug=True)