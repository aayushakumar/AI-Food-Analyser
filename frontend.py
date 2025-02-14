import streamlit as st
from PIL import Image
import pandas as pd
import requests
import re
import plotly.express as px
from io import BytesIO
import time  # Added for progress simulation

# Flask app URL
FLASK_API_URL = "http://127.0.0.1:5000/analyze"

# Define allowed_foods dictionary
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

# Set Streamlit page configuration
st.set_page_config(page_title="🍴 Food Analyzer", page_icon="🍎", layout="wide")

# Define a cohesive color palette
PRIMARY_COLOR = "#FF6347"  # Tomato
SECONDARY_COLOR = "#4B0082"  # Indigo
BACKGROUND_COLOR = "#F0F2F6"  # Light Gray
ACCENT_COLOR = "#20B2AA"  # Light Sea Green

# Custom CSS for better aesthetics
st.markdown(f"""
    <style>
        /* Overall Background */
        .reportview-container {{
            background-color: {BACKGROUND_COLOR};
        }}
        /* Title Styling */
        .title {{
            color: {PRIMARY_COLOR};
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        }}
        /* Footer Styling */
        .footer {{
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
            background-color: {PRIMARY_COLOR};
            color: white;
            text-align: center;
            padding: 10px;
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        }}
        /* Button Styling */
        .stButton>button {{
            color: white;
            background-color: {SECONDARY_COLOR};
        }}
        /* Checkbox Styling */
        .stCheckbox>label {{
            color: {SECONDARY_COLOR};
        }}
    </style>
    """, unsafe_allow_html=True)

# Sidebar for navigation
st.sidebar.title("📋 **Navigation**")
tabs = ["📸 Analyze Food", "🔍 Recipes", "📊 History"]
selected_tab = st.sidebar.radio("Navigate to", tabs)

# Initialize session state
if "uploaded_data_analyze" not in st.session_state:
    st.session_state["uploaded_data_analyze"] = []
if "uploaded_data_recipes" not in st.session_state:
    st.session_state["uploaded_data_recipes"] = []
if "detected_foods" not in st.session_state:
    st.session_state["detected_foods"] = []

# Function to clean ingredient names
def clean_ingredient(ingredient):
    """Remove quantities and normalize ingredient names."""
    ingredient = ingredient.strip().lower()
    units = [
        "cup", "tbsp", "tsp", "g", "kg", "oz", "lb", "liter", "ml", "can", "package",
        "slice", "pinch", "dash", "bunch", "piece", "head", "clove", "sprig", "box"
    ]
    for unit in units:
        if ingredient.startswith(unit + " "):
            ingredient = ingredient.replace(unit + " ", "", 1)
    return ingredient

# Function to clean the value (remove non-numeric characters)
def clean_value(value):
    """
    Cleans the input value by removing non-numeric characters.
    Converts the cleaned string to a float.
    Returns 0.0 if the input is invalid or conversion fails.
    """
    try:
        # Convert the input to string if it's not already
        if not isinstance(value, str):
            value = str(value)
        # Use regex to remove non-numeric characters except the decimal point
        cleaned_value = re.sub(r'[^0-9.]', '', value)
        # Convert the cleaned string to float
        return float(cleaned_value) if cleaned_value else 0.0
    except Exception as e:
        # Log the exception or display an error message
        st.error(f"Error cleaning value: {e}")
        return 0.0

# Analyze Food Tab
if selected_tab == "📸 Analyze Food":
    st.title("📸 **Analyze Food**")
    st.markdown("Upload images of your food to get detailed nutritional information!")
    
    uploaded_files_analyze = st.file_uploader(
        "📤 Upload food images",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True,
        key="uploader_analyze"
    )
    
    if uploaded_files_analyze:
        for uploaded_file in uploaded_files_analyze:
            st.subheader(f"🖼️ Image: {uploaded_file.name}")
            col1, col2 = st.columns([1, 2])
            with col1:
                try:
                    image = Image.open(uploaded_file)
                    st.image(image, caption=uploaded_file.name, use_container_width=True, clamp=True)
                except Exception as e:
                    st.error(f"❌ Error loading image {uploaded_file.name}: {e}")
            with col2:
                quantity = st.number_input(
                    f"📏 Enter quantity in grams for {uploaded_file.name}",
                    min_value=0.0,
                    max_value=5000.0,  # Set an upper limit
                    step=0.05,
                    value=100.0,  # Set default to 100
                    key=f"quantity_analyze_{uploaded_file.name}"
                )
                if st.button("🔍 Get Nutritional Information", key=f"btn_analyze_{uploaded_file.name}"):
                    with st.spinner("⌛ Analyzing..."):
                        progress_bar = st.progress(0)
                        for percent_complete in range(100):
                            time.sleep(0.005)  # Adjust sleep time as needed
                            progress_bar.progress(percent_complete + 1)
                        image_bytes = uploaded_file.getvalue()
                        try:
                            response = requests.post(
                                FLASK_API_URL,
                                files={"image": (uploaded_file.name, image_bytes, uploaded_file.type)}
                            )
                            if response.status_code == 200:
                                data = response.json()
                                detected_foods = data.get("detected_foods", [])
                                macros = data.get("macros per 100g", {})
                                recipes = data.get("recipes", [])

                                if detected_foods:
                                    # Update session state
                                    st.session_state["detected_foods"].extend(detected_foods)

                                    # Aggregate macros across all detected foods
                                    aggregated_macros = {
                                        "calories": 0.0,
                                        "protein": 0.0,
                                        "carbs": 0.0,
                                        "fiber": 0.0
                                    }

                                    for food, food_macros in macros.items():
                                        aggregated_macros["calories"] += clean_value(food_macros.get("calories", '0'))
                                        aggregated_macros["protein"] += clean_value(food_macros.get("protein", '0'))
                                        aggregated_macros["carbs"] += clean_value(food_macros.get("carbs", '0'))
                                        aggregated_macros["fiber"] += clean_value(food_macros.get("fiber", '0'))

                                    # Adjust macros based on quantity
                                    if quantity > 0:
                                        aggregated_macros = {k: (v * quantity) / 100 for k, v in aggregated_macros.items()}
                                    else:
                                        aggregated_macros = {k: 0.0 for k in aggregated_macros}

                                    # Save to uploaded_data_analyze
                                    st.session_state["uploaded_data_analyze"].append({
                                        "Image": uploaded_file.name,
                                        "Quantity (g)": quantity,
                                        "Detected Food(s)": detected_foods,
                                        "Macros": aggregated_macros,
                                    })

                                    # Limit history to last 10 entries
                                    if len(st.session_state["uploaded_data_analyze"]) > 10:
                                        st.session_state["uploaded_data_analyze"].pop(0)

                                    # Display nutritional information
                                    st.markdown(f"### 🍎 **Detected Food**: {', '.join([food.capitalize() for food in detected_foods])}")
                                    macros_data = aggregated_macros

                                    # Display as a table
                                    df_macros = pd.DataFrame.from_dict(macros_data, orient='index', columns=['Amount'])
                                    df_macros.index.name = 'Nutrient'
                                    st.table(df_macros)

                                    # Display macros as an enhanced bar chart
                                    fig = px.bar(
                                        df_macros.reset_index(),
                                        x='Nutrient',
                                        y='Amount',
                                        color='Nutrient',
                                        title='🥗 Nutritional Information',
                                        labels={'Amount': 'Amount per Quantity (g)', 'Nutrient': 'Nutrient'},
                                        color_discrete_sequence=px.colors.qualitative.Vivid
                                    )
                                    fig.update_traces(marker=dict(line=dict(width=1, color='DarkSlateGrey')))
                                    fig.update_layout(showlegend=False)
                                    st.plotly_chart(fig, use_container_width=True)
                                    
                                    # Success message
                                    st.success(f"✅ Successfully analyzed {uploaded_file.name}!")
                                else:
                                    st.warning("⚠️ No food items detected.")
                            else:
                                st.error(f"❌ Error analyzing the image. Status Code: {response.status_code}. Response: {response.text}")
                        except requests.exceptions.ConnectionError:
                            st.error("❌ Could not connect to the analysis server. Make sure the Flask app is running.")
                        except Exception as e:
                            st.error(f"❌ An unexpected error occurred: {e}")
                    progress_bar.empty()

# Recipes Tab (Assuming no Macros are handled here, no changes needed)
elif selected_tab == "🔍 Recipes":
    st.title("🔍 **Discover Recipes**")
    st.markdown("Select ingredients from your analyzed foods or upload new images to find delicious recipes!")
    
    # Option 1: Use detected foods from Analyze Food tab
    st.subheader("📖 **Use Analyzed Foods**")
    if st.session_state["detected_foods"]:
        unique_detected_foods = sorted(list(set(st.session_state["detected_foods"])))
        selected_ingredients = st.multiselect(
            "🔽 Choose ingredients from your analyzed foods:",
            options=unique_detected_foods,
            key="select_ingredients_analyze"
        )
        if st.button("🔍 Find Recipes with Selected Ingredients", key="btn_recipes_analyze"):
            if selected_ingredients:
                with st.spinner("⌛ Fetching recipes..."):
                    progress_bar = st.progress(0)
                    for percent_complete in range(100):
                        time.sleep(0.005)  # Adjust sleep time as needed
                        progress_bar.progress(percent_complete + 1)
                    try:
                        # For each selected ingredient, fetch recipes and aggregate them
                        recipes = []
                        for ingredient in selected_ingredients:
                            params = {"i": ingredient}
                            response = requests.get("https://www.themealdb.com/api/json/v1/1/filter.php", params=params)
                            if response.status_code == 200:
                                recipe_data = response.json()
                                meals = recipe_data.get("meals", [])
                                if meals:
                                    for meal in meals:
                                        recipe = {
                                            'title': meal['strMeal'],
                                            'url': f"https://www.themealdb.com/meal.php?c={meal['idMeal']}",
                                            'image': meal['strMealThumb']
                                        }
                                        recipes.append(recipe)
                        if recipes:
                            # Remove duplicate recipes
                            unique_recipes = {recipe['title']: recipe for recipe in recipes}.values()
                            st.markdown("### 🥗 **Recipes Using Selected Ingredients**")
                            num_columns = 3
                            cols = st.columns(num_columns)
                            for idx, recipe in enumerate(unique_recipes):
                                col = cols[idx % num_columns]
                                with col:
                                    st.image(recipe['image'], width=200, use_container_width=True, clamp=True)
                                    st.markdown(f"**[{recipe['title']}]({recipe['url']})**")
                        else:
                            st.info("ℹ️ No recipes found for the selected ingredients.")
                    except Exception as e:
                        st.error(f"❌ An unexpected error occurred while fetching recipes: {e}")
                progress_bar.empty()
            else:
                st.warning("⚠️ Please select at least one ingredient.")
    else:
        st.info("ℹ️ No detected foods available from the Analyze Food tab. Upload images in the Analyze Food tab first.")
    
    st.markdown("---")
    # Option 2: Upload images to detect new ingredients for recipes
    st.subheader("📷 **Upload Images to Detect Ingredients**")
    uploaded_files_recipes = st.file_uploader(
        "📤 Upload food images to detect ingredients",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True,
        key="uploader_recipes"
    )
    
    if uploaded_files_recipes:
        for uploaded_file in uploaded_files_recipes:
            st.subheader(f"🖼️ Image: {uploaded_file.name}")
            col1, col2 = st.columns([1, 2])
            with col1:
                try:
                    image = Image.open(uploaded_file)
                    st.image(image, caption=uploaded_file.name, use_container_width=True, clamp=True)
                except Exception as e:
                    st.error(f"❌ Error loading image {uploaded_file.name}: {e}")
            with col2:
                quantity = st.number_input(
                    f"📏 Enter quantity in grams for {uploaded_file.name}",
                    min_value=0.0,
                    max_value=5000.0,  # Set an upper limit
                    step=0.05,
                    value=100.0,  # Set default to 100
                    key=f"quantity_recipes_{uploaded_file.name}"
                )
                if st.button("🔍 Detect Ingredients", key=f"btn_detect_{uploaded_file.name}"):
                    with st.spinner("⌛ Analyzing..."):
                        progress_bar = st.progress(0)
                        for percent_complete in range(100):
                            time.sleep(0.005)  # Adjust sleep time as needed
                            progress_bar.progress(percent_complete + 1)
                        image_bytes = uploaded_file.getvalue()
                        try:
                            response = requests.post(
                                FLASK_API_URL,
                                files={"image": (uploaded_file.name, image_bytes, uploaded_file.type)}
                            )
                            if response.status_code == 200:
                                data = response.json()
                                detected_foods = data.get("detected_foods", [])
                                macros = data.get("macros per 100g", {})
                                recipes = data.get("recipes", [])

                                if detected_foods:
                                    # Update session state
                                    st.session_state["detected_foods"].extend(detected_foods)

                                    # Aggregate macros across all detected foods
                                    aggregated_macros = {
                                        "calories": 0.0,
                                        "protein": 0.0,
                                        "carbs": 0.0,
                                        "fiber": 0.0
                                    }

                                    for food, food_macros in macros.items():
                                        aggregated_macros["calories"] += clean_value(food_macros.get("calories", '0'))
                                        aggregated_macros["protein"] += clean_value(food_macros.get("protein", '0'))
                                        aggregated_macros["carbs"] += clean_value(food_macros.get("carbs", '0'))
                                        aggregated_macros["fiber"] += clean_value(food_macros.get("fiber", '0'))

                                    # Adjust macros based on quantity
                                    if quantity > 0:
                                        aggregated_macros = {k: (v * quantity) / 100 for k, v in aggregated_macros.items()}
                                    else:
                                        aggregated_macros = {k: 0.0 for k in aggregated_macros}

                                    # Save to uploaded_data_recipes
                                    st.session_state["uploaded_data_recipes"].append({
                                        "Image": uploaded_file.name,
                                        "Quantity (g)": quantity,
                                        "Detected Food(s)": detected_foods,
                                        "Macros": aggregated_macros,
                                    })

                                    # Limit history to last 10 entries
                                    if len(st.session_state["uploaded_data_recipes"]) > 10:
                                        st.session_state["uploaded_data_recipes"].pop(0)

                                    # Display detected foods
                                    st.markdown(f"### 🍎 **Detected Food**: {', '.join([food.capitalize() for food in detected_foods])}")
                                    
                                    # Success message
                                    st.success(f"✅ Successfully detected ingredients in {uploaded_file.name}!")
                                else:
                                    st.warning("⚠️ No food items detected.")
                            else:
                                st.error(f"❌ Error analyzing the image. Status Code: {response.status_code}. Response: {response.text}")
                        except requests.exceptions.ConnectionError:
                            st.error("❌ Could not connect to the analysis server. Make sure the Flask app is running.")
                        except Exception as e:
                            st.error(f"❌ An unexpected error occurred: {e}")
                    progress_bar.empty()
    
    # Allow selecting from all detected foods (from both tabs)
    if st.session_state["detected_foods"]:
        st.markdown("---")
        st.subheader("🔍 **Select Ingredients from All Detected Foods**")
        selected_ingredients_combined = st.multiselect(
            "🔽 Choose ingredients from all detected foods:",
            options=sorted(list(set(st.session_state["detected_foods"]))),
            key="select_ingredients_combined"
        )
        if st.button("🔍 Find Recipes with Selected Ingredients", key="btn_recipes_combined"):
            if selected_ingredients_combined:
                with st.spinner("⌛ Fetching recipes..."):
                    progress_bar = st.progress(0)
                    for percent_complete in range(100):
                        time.sleep(0.005)  # Adjust sleep time as needed
                        progress_bar.progress(percent_complete + 1)
                    try:
                        recipes = []
                        for ingredient in selected_ingredients_combined:
                            params = {"i": ingredient}
                            response = requests.get("https://www.themealdb.com/api/json/v1/1/filter.php", params=params)
                            if response.status_code == 200:
                                recipe_data = response.json()
                                meals = recipe_data.get("meals", [])
                                if meals:
                                    for meal in meals:
                                        recipe = {
                                            'title': meal['strMeal'],
                                            'url': f"https://www.themealdb.com/meal.php?c={meal['idMeal']}",
                                            'image': meal['strMealThumb']
                                        }
                                        recipes.append(recipe)
                        if recipes:
                            # Remove duplicate recipes
                            unique_recipes = {recipe['title']: recipe for recipe in recipes}.values()
                            st.markdown("### 🥗 **Recipes Using Selected Ingredients**")
                            num_columns = 3
                            cols = st.columns(num_columns)
                            for idx, recipe in enumerate(unique_recipes):
                                col = cols[idx % num_columns]
                                with col:
                                    st.image(recipe['image'], width=200, use_container_width=True, clamp=True)
                                    st.markdown(f"**[{recipe['title']}]({recipe['url']})**")
                        else:
                            st.info("ℹ️ No recipes found for the selected ingredients.")
                    except Exception as e:
                        st.error(f"❌ An unexpected error occurred while fetching recipes: {e}")
                progress_bar.empty()
            else:
                st.warning("⚠️ Please select at least one ingredient.")

# History Tab
elif selected_tab == "📊 History":
    st.title("📊 **Past Uploads and Analyses**")
    
    history_tabs = ["🔍 Analyze Food History", "🔍 Recipes History"]
    history_selected_tab = st.tabs(history_tabs)
    
    # Analyze Food History
    with history_selected_tab[0]:
        st.subheader("🔍 **Analyze Food History**")
        if st.session_state["uploaded_data_analyze"]:
            data_analyze = pd.DataFrame(st.session_state["uploaded_data_analyze"])
            
            # Convert 'Detected Food(s)' list to comma-separated string
            data_analyze['Detected Food(s)'] = data_analyze['Detected Food(s)'].apply(lambda x: ', '.join(x))
            
            # Define required macros
            required_macros = ["calories", "protein", "carbs", "fiber"]
            
            # Initialize an empty list to collect all macros
            macros_list = []
            for macros in data_analyze['Macros']:
                # Ensure all required macros are present, else set to 0.0
                macro_entry = {macro: macros.get(macro, 0.0) for macro in required_macros}
                # Ensure all values are floats
                for macro in required_macros:
                    try:
                        macro_entry[macro] = float(macro_entry[macro])
                    except:
                        macro_entry[macro] = 0.0
                macros_list.append(macro_entry)
            
            # Create a DataFrame from the macros
            macros_df = pd.DataFrame(macros_list)
            
            # Concatenate with the main DataFrame
            data_analyze_flat = pd.concat([data_analyze.drop('Macros', axis=1), macros_df], axis=1)
            
            # Ensure macro columns are floats
            for macro in required_macros:
                data_analyze_flat[macro] = pd.to_numeric(data_analyze_flat[macro], errors='coerce').fillna(0.0)
            
            # Display the flattened DataFrame with styling on macro columns only
            try:
                st.dataframe(data_analyze_flat.style.highlight_max(subset=required_macros, axis=0))
            except ValueError as e:
                st.error(f"Error in styling DataFrame: {e}")
                st.dataframe(data_analyze_flat)  # Show DataFrame without styling for debugging
            
            # Visualizations
            st.markdown("### 📈 **Detected Foods Distribution (Analyze Food)**")
            # Flatten list of detected foods
            detected_foods = [food for sublist in st.session_state["uploaded_data_analyze"] for food in sublist['Detected Food(s)']]
            food_counts_analyze = pd.Series(detected_foods).value_counts().reset_index()
            food_counts_analyze.columns = ['Food Item', 'Count']
            fig_analyze = px.bar(
                food_counts_analyze,
                x='Food Item',
                y='Count',
                title='Frequency of Detected Foods (Analyze Food)',
                labels={'Food Item': 'Food Item', 'Count': 'Count'},
                color='Count',
                color_continuous_scale='Viridis'
            )
            fig_analyze.update_layout(showlegend=False)
            st.plotly_chart(fig_analyze, use_container_width=True)

            st.markdown("### 🥦 **Macronutrients Overview (Analyze Food)**")
            macros_sum_analyze = macros_df.sum().reset_index()
            macros_sum_analyze.columns = ['Nutrient', 'Total Amount']
            fig_macros_analyze = px.pie(
                macros_sum_analyze,
                names='Nutrient',
                values='Total Amount',
                title='Total Macronutrients Consumed (Analyze Food)',
                color_discrete_sequence=px.colors.sequential.RdBu
            )
            st.plotly_chart(fig_macros_analyze, use_container_width=True)
            
            # Clear History Button
            if st.button("🗑️ Clear Analyze Food History"):
                st.session_state["uploaded_data_analyze"] = []
                st.success("✅ Analyze Food History cleared.")
        else:
            st.info("ℹ️ No Analyze Food uploads to display.")
    
    # Recipes History
    with history_selected_tab[1]:
        st.subheader("🔍 **Recipes History**")
        if st.session_state["uploaded_data_recipes"]:
            data_recipes = pd.DataFrame(st.session_state["uploaded_data_recipes"])
            st.dataframe(data_recipes)
            
            # You can add visualizations for recipes history if desired
            
            # Clear History Button
            if st.button("🗑️ Clear Recipes History"):
                st.session_state["uploaded_data_recipes"] = []
                st.success("✅ Recipes History cleared.")
        else:
            st.info("ℹ️ No Recipes uploads to display.")

# Footer
st.markdown(f"""
    <div class="footer">
        <p>Food Analyzer App | Final Project For CS415</p>
        <p>Developed by Chesta, Aayush, Meghan</p>
    </div>
    """, unsafe_allow_html=True)
