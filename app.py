from flask import Flask, request, render_template
import pandas as pd
import random
from flask_sqlalchemy import SQLAlchemy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)

# Flask App Configurations
app.secret_key = "alskdjfwoeieiurlskdjfslkdjf"
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://root:amrsubshe19@localhost:3306/ecom"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# SQLAlchemy Models
class Signup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)

class Signin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)

# Utility functions
def truncate(text, length):
    """Truncate product names for display."""
    return text[:length] + "..." if len(text) > length else text

def clean_image_url(url):
    """Clean the ImageURL column to pick only the first valid URL."""
    if isinstance(url, str):
        return url.split(" | ")[0].strip()  # Take the first URL and remove extra spaces
    return url

def content_based_recommendations(dataframe, search_term, top_n=10):
    """Generate product recommendations based on content similarity."""
    search_term = search_term.lower()
    for column in ['Name', 'Category', 'Tags', 'Description']:
        dataframe[column] = dataframe[column].fillna('').str.lower()

    matching_items = dataframe[
        dataframe['Name'].str.contains(search_term, na=False) |
        dataframe['Category'].str.contains(search_term, na=False) |
        dataframe['Tags'].str.contains(search_term, na=False) |
        dataframe['Description'].str.contains(search_term, na=False)
    ]

    if matching_items.empty:
        return pd.DataFrame()

    dataframe['CombinedText'] = (
        dataframe['Name'] + ' ' +
        dataframe['Category'] + ' ' +
        dataframe['Tags'] + ' ' +
        dataframe['Description']
    )

    tfidf_vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf_vectorizer.fit_transform(dataframe['CombinedText'])
    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)

    matched_index = matching_items.index[0]
    similarity_scores = list(enumerate(cosine_sim[matched_index]))
    similarity_scores = sorted(similarity_scores, key=lambda x: x[1], reverse=True)
    top_similar_indices = [i[0] for i in similarity_scores[1:top_n + 1]]

    return dataframe.iloc[top_similar_indices][[
        'ID', 'ProdID', 'Name', 'Category', 'Tags', 'Description', 'Brand', 'ReviewCount', 'ImageURL', 'Rating'
    ]]

# Random Image URLs for demonstration purposes
random_image_urls = [
    "static/img/img_1.png", "static/img/img_2.png", "static/img/img_3.png",
    "static/img/img_4.png", "static/img/img_5.png", "static/img/img_6.png",
    "static/img/img_7.png", "static/img/img_8.png"
]

@app.route("/filter_by_rating", methods=['GET'])
def filter_by_rating():
    try:
        # Load product data dynamically from the database
        product_data_query = "SELECT * FROM clean_data"  # Replace with your actual table name
        train_data = pd.read_sql(product_data_query, db.engine)

        # Clean ImageURL column
        train_data['ImageURL'] = train_data['ImageURL'].apply(clean_image_url)

        # Get the minimum rating from query parameters
        min_rating = float(request.args.get('rating', 0))  # Default to 0 if no rating is provided

        # Filter products by rating
        filtered_products = train_data[train_data['Rating'] >= min_rating]

        if filtered_products.empty:
            message = "No products found with the selected rating or higher."
            return render_template('main.html', message=message)

        # Randomize product images for display
        random_product_image_urls = [random.choice(random_image_urls) for _ in range(len(filtered_products))]
        price = [40, 50, 60, 70, 100, 122, 106, 50, 30, 50]

        return render_template('main.html', content_based_rec=filtered_products, truncate=truncate,
                               random_product_image_urls=random_product_image_urls,
                               random_price=random.choice(price))
    except Exception as e:
        return f"Error filtering by rating: {e}"


# Routes
@app.route("/")
def index():
    try:
        # Load trending products dynamically from the database
        trending_products_query = "SELECT * FROM trending_products"  # Replace with your actual table name
        trending_products = pd.read_sql(trending_products_query, db.engine)

        # Clean ImageURL column
        trending_products['ImageURL'] = trending_products['ImageURL'].apply(clean_image_url)

        random_product_image_urls = [random.choice(random_image_urls) for _ in range(len(trending_products))]
        price = [40, 50, 60, 70, 100, 122, 106, 50, 30, 50]

        return render_template('index.html', trending_products=trending_products.head(8), truncate=truncate,
                               random_product_image_urls=random_product_image_urls, random_price=random.choice(price))
    except Exception as e:
        return f"Error loading trending products: {e}"

@app.route("/main")
def main():
    return render_template('main.html')

@app.route("/signup", methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        new_signup = Signup(username=username, email=email, password=password)
        db.session.add(new_signup)
        db.session.commit()

        return index()
    return render_template('signup.html')

@app.route("/signin", methods=['POST', 'GET'])
def signin():
    if request.method == 'POST':
        username = request.form['signinUsername']
        password = request.form['signinPassword']

        new_signin = Signin(username=username, password=password)
        db.session.add(new_signin)
        db.session.commit()

        return index()
    return render_template('signin.html')

# @app.route("/recommendations", methods=['POST', 'GET'])
# def recommendations():
#     try:
#         # Load product data dynamically from the database
#         product_data_query = "SELECT * FROM clean_data"  # Replace with your actual table name
#         train_data = pd.read_sql(product_data_query, db.engine)

#         # Clean ImageURL column
#         train_data['ImageURL'] = train_data['ImageURL'].apply(clean_image_url)

#         if request.method == 'POST':
#             prod = request.form.get('prod')
#             nbr = int(request.form.get('nbr'))
#             content_based_rec = content_based_recommendations(train_data, prod, top_n=nbr)

#             if content_based_rec.empty:
#                 message = "No recommendations available for this product."
#                 return render_template('main.html', message=message)

#             random_product_image_urls = [random.choice(random_image_urls) for _ in range(len(content_based_rec))]
#             price = [40, 50, 60, 70, 100, 122, 106, 50, 30, 50]
#             return render_template('main.html', content_based_rec=content_based_rec, truncate=truncate,
#                                    random_product_image_urls=random_product_image_urls,
#                                    random_price=random.choice(price))
#         return render_template('main.html')
#     except Exception as e:
#         return f"Error generating recommendations: {e}"
@app.route("/recommendations", methods=['POST', 'GET'])
def recommendations():
    try:
        # Load product data dynamically from the database
        product_data_query = "SELECT * FROM clean_data"  # Replace with your actual table name
        train_data = pd.read_sql(product_data_query, db.engine)

        # Clean ImageURL column
        train_data['ImageURL'] = train_data['ImageURL'].apply(clean_image_url)

        if request.method == 'POST':
            prod = request.form.get('prod')  # Get search term
            nbr = int(request.form.get('nbr'))  # Number of recommendations
            min_rating = float(request.form.get('rating', 0))  # Minimum rating (default to 0)

            # Fetch the rating of the product being searched for
            searched_product = train_data[train_data['Name'].str.contains(prod, case=False, na=False)]

            if searched_product.empty:
                message = f"No product found for '{prod}'."
                return render_template('main.html', message=message)

            # Get the rating of the first matching product (you can adjust logic if needed)
            searched_product_rating = searched_product.iloc[0]['Rating']

            # Ensure the rating used for filtering is at least the searched product's rating
            min_rating = max(min_rating, searched_product_rating)

            # Generate recommendations
            content_based_rec = content_based_recommendations(train_data, prod, top_n=nbr)

            # Ensure Rating column is numeric
            content_based_rec['Rating'] = pd.to_numeric(content_based_rec['Rating'], errors='coerce')

            # Filter recommendations by the minimum rating (greater than or equal to searched product rating)
            filtered_recommendations = content_based_rec[content_based_rec['Rating'] >= min_rating]

            # Ensure recommendations exist after filtering
            if filtered_recommendations.empty:
                message = "No recommendations available for this product with the selected rating."
                return render_template('main.html', message=message)

            # Randomize product images for display
            random_product_image_urls = [
                random.choice(random_image_urls) for _ in range(len(filtered_recommendations))
            ]
            price = [40, 50, 60, 70, 100, 122, 106, 50, 30, 50]

            return render_template(
                'main.html',
                content_based_rec=filtered_recommendations,
                truncate=truncate,
                random_product_image_urls=random_product_image_urls,
                random_price=random.choice(price),
                message=None  # No need to pass a message if recommendations are available
            )

        return render_template('main.html', message=None)  # Initial page render

    except Exception as e:
        return f"Error generating recommendations: {e}"

if __name__ == '__main__':
    app.run(debug=True)



