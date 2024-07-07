import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

API_KEY = os.getenv("API_KEY") or "sk-XXXX"

client = OpenAI(
    api_key=API_KEY
)
prompt='''A picture of the following dish:
  {
  "id": 141,
  "recipeName": "Pasta with Meatballs",
  
  "instructions": [
    {
      "number": 1,
      "description": "Preheat your oven to 400°F (200°C)."
    },
    {
      "number": 2,
      "description": "In a large mixing bowl, combine the ground beef, chopped onion, minced garlic, egg, breadcrumbs, oregano, salt, and pepper. Mix well with your hands or a wooden spoon until just combined. Don't overmix!"
    },
    {
      "number": 3,
      "description": "Use your hands to shape the mixture into small meatballs, about 1 1/2 inches in diameter. You should end up with around 20-25 meatballs."
    },
    {
      "number": 4,
      "description": "Place the meatballs on a baking sheet lined with parchment paper, leaving a little space between each one. Drizzle with a tablespoon of olive oil and gently roll them around to coat evenly."
    },
    {
      "number": 5,
      "description": "Bake the meatballs in the preheated oven for 18-20 minutes, or until cooked through and lightly browned on the outside."
    },
    {
      "number": 6,
      "description": "While the meatballs are baking, cook your pasta according to the package instructions until al dente. Drain and set aside."
    },
    {
      "number": 7,
      "description": "In a large saucepan, heat the marinara sauce over medium heat. Add the cooked pasta and toss to combine."
    },
    {
      "number": 8,
      "description": "Add the baked meatballs to the saucepan and toss everything together until the meatballs are well coated with the sauce."
    },
    {
      "number": 9,
      "description": "Sprinkle the Parmesan cheese over the top and toss gently to combine."
    },
    {
      "number": 10,
      "description": "Serve hot, garnished with chopped parsley if desired."
    }
  ]
}'''
response = client.images.generate(
  model="dall-e-3", # "dall-e-2", "dall-e-3"
  prompt=prompt,
  size="1792x1024", #"1024x1024", "1024x1792" or "1792x1024"
  quality="standard", #"hd", "standard"
  n=1,
)

image_url = response.data[0].url

print(response)