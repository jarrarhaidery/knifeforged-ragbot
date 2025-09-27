import requests
from requests.auth import HTTPBasicAuth

url = "https://knifeforged.shop/wp-json/wc/v3/products?per_page=1"
consumer_key = "ck_8d4aa282b3930547b678f11b600816c0b7b98ff6"
consumer_secret = "cs_533d2fdf2cdb3ba148225b0489212fdda59665bb"

response = requests.get(url, auth=HTTPBasicAuth(consumer_key, consumer_secret))

print("Status:", response.status_code)
print("Response:", response.text)
