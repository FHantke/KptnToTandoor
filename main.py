import click
import requests
import uuid
import sys
from urllib.parse import urlparse

# TODO error handling...

def get_kptn_recipe(uid):
    """ Get the recipe JSON from KptnCook """

    url = "https://mobile.kptncook.com:443/recipes/search?lang=de&store=de"
    headers = {
        "hasIngredients": "YES",
        "kptnkey": "6q7QNKy-oIgk-IMuWisJ-jfN7s6",
        "Accept": "application/vnd.kptncook.mobile-v8+json",
        "User-Agent": "Platform/Android/5.0.1 App/7.2.7",
    }

    res = requests.post(url, headers=headers, json=[{"uid": uid}])   
    if res.status_code != 200:
        return None

    return res.json()

def import_recipe(host, auth, data, with_time=False):
    """ Take the KptnCook JSON and translate it to Tandoor """

    headers = {"Authorization": "Token " + auth}

    # d is the final JSON
    d = {}
    d["name"] = data["title"]
    d["description"] = data["authorComment"]
    d["keywords"] = []  # add your own keywords
    d["internal"] = True
    d["nutrition"] = {
        "calories": data["recipeNutrition"]["calories"],
        "proteins": data["recipeNutrition"]["protein"],
        "fats": data["recipeNutrition"]["fat"],
        "carbohydrates": data["recipeNutrition"]["carbohydrate"],
    }

    d["working_time"] = data.get("preparationTime", 0)
    d["waiting_time"] = data.get("cookingTime", 0)
    d["servings"] = 1    
    d["file_path"] = ""  # Is added below

    # Parse all steps
    steps = []
    for step_idx, s in enumerate(data["steps"]):        
        # Init data
        step = {}
        step["instruction"] = s["title"]
        step["step_recipe"] = None        
        step["order"] = step_idx
        step["show_as_header"] = True

        # Load the step image and upload it to Tandoor
        img_url = s["image"]["url"]        
        res = requests.get(img_url , params={"kptnkey": "6q7QNKy-oIgk-IMuWisJ-jfN7s6"}, stream=True)
        bin_data = res.content        
        img_name = str(uuid.uuid4())
        files = {'file': (img_name + '.png', bin_data)}
        res = requests.post(host.strip("/") + "/api/user-file/", headers=headers, files=files, data={"name": img_name})
        if res.status_code != 201:
            print(res.text)
            sys.exit(1)

        step["file"] = res.json()

        # Parse the time per step
        step["time"] = 0
        timers = s["timers"]
        for timer in timers:
            t = timer["minOrExact"]
            if with_time:
                step["time"] += t
            if "max" in timer:
                t_str = f"{ t } - { timer['max'] } min."
            else:
                t_str = f"{ t } min."
            step["instruction"] = step["instruction"].replace("<timer>", t_str, 1)

        # Parse all ingredients
        ingredients = []
        ings = s.get("ingredients", [])
        for ing_idx, ing in enumerate(ings):
            # Init ingredient
            ingredient = {}            
            ingredient["note"] = ""
            ingredient["order"] = ing_idx
            ingredient["is_header"] = False
            ingredient["no_amount"] = False

            # Add the food. If name already exists, Tandoor will merge it.
            ingredient["food"] = {
                "full_name": ing["title"],
                "name": ing["title"],
                "food_onhand": False,
                "supermarket_category": None,
                "inherit_fields": [],
                "ignore_shopping": False
            }

            # Init measures and units   
            ingredient["amount"] = 0
            ingredient["unit"] = None
            ingredient["no_amount"] = True

            # Parse measures and units 
            if "unit" in ing:                
                ingredient["amount"] = ing["unit"]["quantity"]
                ingredient["no_amount"] = False
                if "measure" in ing["unit"]:
                    ingredient["unit"] = {"name": ing["unit"]["measure"]}
            elif "quantity" in ing:
                ingredient["amount"] = ing["quantity"]
                ingredient["no_amount"] = False
            
            # Add ingredient
            ingredients.append(ingredient)

        # Add step
        step["ingredients"] = ingredients
        steps.append(step)
    
    # Add steps
    d["steps"] = steps
    
    # Upload recipe to Tandoor
    recipe_api_url = host.strip("/") + "/api/recipe/"
    res = requests.post(recipe_api_url, headers=headers, json=d)
    if res.status_code != 201:
        print(res.text)
        sys.exit(1)

    # Get recipe id to upload the cover image
    res_data = res.json()
    rid = res_data["id"]
    img_api_url = host.strip("/") + f"/api/recipe/{rid}/image/"
    
    # Loading the cover image from KptnCook
    for img in data["imageList"]:
        if img["type"] == "cover":
            img_url = img["url"]
            break
    
    res = requests.get(img_url , params={"kptnkey": "6q7QNKy-oIgk-IMuWisJ-jfN7s6"}, stream=True)
    bin_data = res.content

    # Upload cover image to Tandoor
    files = {'image': ('img.png', bin_data)}
    res = requests.put(img_api_url, headers=headers, files=files)
    if res.status_code != 200:
        print(res.text)
        sys.exit(1)

    # Link cover image with recipe
    d["file_path"] = host.strip("/") + res.json()["image"]    
    res = requests.put(recipe_api_url + str(rid), headers=headers, json=d)
    if res.status_code != 200:
        print(res.text)
        sys.exit(1)


@click.command()
@click.argument('host')
@click.argument('api_key')
@click.argument('src')
@click.option('--with_time', default=False, help='import time into recipes')
def main(host, api_key, src, with_time):
    """Request a recipe (<SRC>) from KptnCook and
       import it into the Tandoor cookbook on <HOST>
       using the Tandoor <API_KEY>.
       <SRC> can either be the recipe id or the shared recipe url."""

    # Get UID
    uid = src
    if src.startswith("http"):        
        print("Try to parse URL")
        res = requests.get(src, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:10.0) Gecko/20100101 Firefox/10.0"})
        u = urlparse(res.url)
        uid = u.path.split("/")[-1]
        print(f"Loading recipe from {res.url}")

    print(f"UID: {uid}")
    data = get_kptn_recipe(uid)

    if not data:
        print("No data were parsed")
        sys.exit(1)

    print(f"Start parsing and uploading")
    import_recipe(host, api_key, data[0], with_time=with_time)
    
    print(f"Done!")

if __name__ == '__main__':
    main()