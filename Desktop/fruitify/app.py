from flask import Flask, render_template
import os

app = Flask(__name__)
@app.route('/')
def home():
    products = [
    {"name": "Strawberries", "price": "Rs. 250/kg", "image": "strawberries.jpg", "category": "seasonal", "label": "Best Seller","stock": "In Stock"},
    {"name": "Mangoes", "price": "Rs. 180/kg", "image": "mangoes.jpg","category": "seasonal", "label": "Best Seller","stock": "Out of Stock"},
    {"name": "Apples", "price": "Rs. 200/kg", "image": "apples.jpg","category": "tropical", "label": "Seasonal","stock": "In Stock"},
    {"name": "Bananas", "price": "Rs. 120/dozen", "image": "bananas.jpg","category": "tropical", "label": "Seasonal","stock": "In Stock"},
    {"name": "Oranges", "price": "Rs. 150/kg", "image": "oranges.jpg","category": "seasonal", "label": "Best Seller","stock": "In Stock"},
    {"name": "Grapes", "price": "Rs. 220/kg", "image": "grapes.jpg","category": "tropical", "label": "Seasonal","stock": "Out of Stock"},
    {"name": "Pineapples", "price": "Rs. 300/each", "image": "pineapples.jpg","category": "local", "label": "New","stock": "In Stock"},
    {"name": "Watermelons", "price": "Rs. 350/each", "image": "watermelons.jpg","category": "tropical", "label": "Seasonal","stock": "Out of Stock"},
    {"name": "Papayas", "price": "Rs. 180/each", "image": "papayas.jpg","category": "tropical", "label": "Seasonal","stock": "In Stock"},
    {"name": "Peaches", "price": "Rs. 240/kg", "image": "peaches.jpg","category": "seasonal", "label": "Best Seller","stock": "In Stock"},
    {"name": "Pomegranates", "price": "Rs. 280/kg", "image": "pomegranates.jpg","category": "seasonal", "label": "Best Seller","stock": "In Stock"},
    {"name": "Blueberries", "price": "Rs. 400/box", "image": "blueberries.jpg","category": "local", "label": "New","stock": "In Stock"}
]
    return render_template('index.html',products=products)


if __name__ == '__main__':
    app.run(debug=True)

    