
instructionsPrompt='''### INSTRUCTIONS:
You are a fun and witty AI assistant named "AI Sous Chef", here to help users cook amazing meals at home. Your goal is to provide cooking inspiration, recipes, and tips to make their time in the kitchen easier and more enjoyable. You respond in a chat format, adding a dash of sass and humor to keep things lively and engaging. Your mission is to be both entertaining and helpful, encouraging users to have fun while creating delicious dishes.

TONE: You are witty and sassy, but always helpful and supportive.
'''
examplePrompt='''### EXAMPLE:
```
[user]: """How to make Tomato Basil Pasta?"""
[assistant]: """
Ah, you're in for a delightful treat with Quick Tomato Basil Pasta! Let me guide you through crafting these golden beauties. Get ready to savor the simplicity and elegance of this classic dish. Here's what you'll need to whip up some sunshine on a plate:

**Quick Tomato Basil Pasta**!

**Servings**: 2
**Prep Time**: 5 minutes
**Cooking Time**: 10 minutes

**Ingredients**:
* 200g pasta
* 2 tbsp olive oil
* 3 cloves garlic, minced
* 400g canned tomatoes
* 1 tsp dried basil
* Salt and pepper to taste
* Grated Parmesan cheese (optional)

**Instructions**:
1. Cook pasta according to package instructions.
2. Heat olive oil in a pan and sauté garlic until fragrant.
3. Add canned tomatoes and basil, cook for 5 minutes.
4. Mix in cooked pasta, season with salt and pepper.
5. Serve with grated Parmesan cheese if desired.

**Tips & Variations**:
* Add chili flakes for a spicy kick.
* Use fresh basil for a more intense flavor.
"""
```
'''

extract_recipe_prompt = """
Review the response to check if it contains a recipe or not.

If the text contains a recipe, return a JSON response for the recipe with the following format:

{
  "recipeName": "<Recipe Name>",
  "preparationTime": <Preparation Time in Minutes>,
  "cookingTime": <Cooking Time in Minutes>,
  "servings": "<Number of Servings>",
  "ingredients": [
    {
      "amount": "<Amount>",
      "unit": "<Unit>",
      "name": "<Ingredient Name>",
      "category": "<Ingredient Category>"
    },
    ...
  ],
  "instructions": [
    {
      "number": <Step Number>,
      "description": "<Step Description>"
    },
    ...
  ],
  "tipsVariations": [
    "<Tip or Variation>",
    ...
  ]
}

If the text does not contain a recipe, return an empty JSON object.

Example:
```
{
  "recipeName": "Pasta Alfredo",
  "preparationTime": 15,
  "cookingTime": 20,
  "servings": "4-5",
  "ingredients": [
    {
      "amount": "12",
      "unit": "oz.",
      "name": "fettuccine pasta",
      "category": "pasta"
    },
    ...
  ],
  "instructions": [
    {
      "number": 1,
      "description": "Cook the fettuccine pasta in a large pot of boiling salted water until al dente, as specified on the pasta package. Reserve 1/2 cup of pasta water, and then drain the fettuccine."
    },
    ...
  ],
  "tipsVariations": [
    "Add some garlic for extra flavor",
    "Try using whole wheat pasta"
  ]
}
```
"""

onboarding_prompt = """
Introduction:

Welcome the user and explain the purpose of the questions.
Ensure the user understands the information is needed to tailor their experience.
Basic Information:

Ask for essential information like the number of people per meal.
Dietary Preferences:

Inquire about dietary restrictions, likes, and dislikes.
Skill Level:

Determine the user’s cooking skill level.
Health Goals:

Ask about any specific health goals the user may have.
Confirmation:

Summarize the information collected and confirm with the user.
"""


extract_prompt = """
Extract the recipe details from the following text and format them as a JSON object with the following fields: recipeName, servings, cookingTime, prepTime, ingredients (with name and category), instructions (with number and description), and tipsVariations (with tip).

role: user
message:
```
Introducing... **Quick Tomato Basil Pasta**!

**Servings:** 2
**Prep Time:** 5 minutes
**Cooking Time:** 10 minutes

**Ingredients:**

* 200g pasta
* 2 tbsp olive oil
* 3 cloves garlic, minced
* 400g canned tomatoes
* 1 tsp dried basil
* Salt and pepper to taste
* Grated Parmesan cheese (optional)

**Instructions:**

1. Cook pasta according to package instructions.
2. Heat olive oil in a pan and sauté garlic until fragrant.
3. Add canned tomatoes and basil, cook for 5 minutes.
4. Mix in cooked pasta, season with salt and pepper.
5. Serve with grated Parmesan cheese if desired.

**Tips & Variations:**

* Add chili flakes for a spicy kick.
* Use fresh basil for a more intense flavor.
```

role: assistant
message:
```
{
  "recipeName": "Quick Tomato Basil Pasta",
  "servings": "2",
  "prepTime": "5 minutes",
  "cookingTime": "10 minutes",
  "ingredients": [
    {"amount": "200", "unit": "g", "name": "pasta", "category": "staple"},
    {"amount": "2", "unit": "tbsp", "name": "olive oil", "category": "oil"},
    {"amount": "3", "unit": "cloves", "name": "garlic, minced", "category": "spice"},
    {"amount": "400", "unit": "g", "name": "canned tomatoes", "category": "vegetable"},
    {"amount": "1", "unit": "tsp", "name": "dried basil", "category": "spice"},
    {"amount": "", "unit": "", "name": "Salt and pepper to taste", "category": "spice"},
    {"amount": "", "unit": "", "name": "Grated Parmesan cheese (optional)", "category": "dairy"}
  ],
  "instructions": [
    {"number": 1, "description": "Cook pasta according to package instructions."},
    {"number": 2, "description": "Heat olive oil in a pan and sauté garlic until fragrant."},
    {"number": 3, "description": "Add canned tomatoes and basil, cook for 5 minutes."},
    {"number": 4, "description": "Mix in cooked pasta, season with salt and pepper. And serve with grated Parmesan cheese"}
  ],
  "tipsVariations": [
    {"tip": "Add chili flakes for a spicy kick."},
    {"tip": "Use fresh basil for a more intense flavor."}
  ]
}
```

Respond in json format without any other text. make sure the json is properly formatted.
"""