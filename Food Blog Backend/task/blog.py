import sqlite3
import sys
import argparse

parser = argparse.ArgumentParser()

parser.add_argument("--ingredients")
parser.add_argument("--meals")
parser.add_argument("food_blog.db")

arguments = parser.parse_args()

# args = sys.argv
# database_name = args[1]
database_name = "food_blog.db"

connection = sqlite3.connect(database_name)
cursor = connection.cursor()

cursor.execute("""Create table if not exists meals(
                            meal_id integer Primary Key,
                            meal_name text not null unique);""")
cursor.execute("""Create table if not exists ingredients(
                    ingredient_id integer primary key,
                    ingredient_name text unique not null);""")
cursor.execute("""Create table if not exists measures(
                    measure_id integer primary key,
                    measure_name text unique);""")
cursor.execute("""Create table if not exists recipes(
                    recipe_id integer primary key,
                    recipe_name text not null,
                    recipe_description text);""")
cursor.execute("PRAGMA foreign_keys = ON;")
cursor.execute("""Create table if not exists serve(
                    serve_id integer primary key,
                    meal_id integer not null,
                    recipe_id integer not null,
                    Foreign key (meal_id) References meals(meal_id),
                    foreign key (recipe_id) references recipes(recipe_id));""")
cursor.execute("""Create table if not exists quantity(
                    quantity_id integer primary key,
                    quantity integer not null,
                    measure_id integer not null,
                    recipe_id integer not null,
                    ingredient_id integer not null,
                    Foreign key (measure_id) References measures(measure_id),
                    foreign key (recipe_id) references recipes(recipe_id),
                    foreign key (ingredient_id) references ingredients (ingredient_id));""")

connection.commit()


if arguments.ingredients is None and arguments.meals is None:
    data = {"meals": ("breakfast", "brunch", "lunch", "supper"),
            "ingredients": ("milk", "cacao", "strawberry", "blueberry", "blackberry", "sugar"),
            "measures": ("ml", "g", "l", "cup", "tbsp", "tsp", "dsp", "")}
    for table, rows in data.items():
        query = "Insert into " + table + " (" + table[:-1] + "_name) values "
        for element in rows:
            query += "('" + element + "'),"
        query = query[:-1] + ";"
        cursor.execute(query)
        connection.commit()
    print("Pass the empty recipe name to exit.")

    result = cursor.execute("Select meal_id, meal_name from meals")
    all_rows = result.fetchall()
    meal_options = ""
    for index, meal in all_rows:
        meal_options += str(index) + ") " + meal + " "

    while True:
        name = input("Recipe name: ")
        if name != "":
            description = input("Recipe description: ")
            recipe_id = cursor.execute("Insert into recipes (recipe_name, recipe_description) values ('" + name + "', '" + description + "');").lastrowid
            print(meal_options)
            meals = input("When the dish can be served: ").split()
            for meal_id in meals:
                cursor.execute("Insert into serve (meal_id, recipe_id) values (" + meal_id + ", " + str(recipe_id) + ");")

            while True:
                ingredient = input("Input quantity of ingredient <press enter to stop>: ")
                if ingredient != "":
                    results = ingredient.split()
                    if len(results) == 2:
                        qty, ing = results[0], results[1]
                        meas = ''
                        measure_id = 8
                    else:
                        qty, meas, ing = results[0], results[1], results[2]
                    ing_results = cursor.execute("Select ingredient_id from ingredients where ingredient_name like '%" + ing + "%';").fetchall()
                    if len(ing_results) == 1:
                        ingredient_id = ing_results[0][0]
                        if meas != '':
                            meas_results = cursor.execute("Select measure_id from measures where measure_name like '" + meas + "%';").fetchall()
                            if len(meas_results) == 1:
                                measure_id = meas_results[0][0]
                                cursor.execute("Insert into quantity (quantity, recipe_id, measure_id, ingredient_id) values (" + str(qty) + ", " + str(recipe_id) + ", " + str(measure_id) + ", " + str(ingredient_id) + ");")
                                connection.commit()
                            else:
                                print("The measure is not conclusive!")
                        else:
                            cursor.execute("Insert into quantity (quantity, recipe_id, measure_id, ingredient_id) values (" + str(qty) + ", " + str(recipe_id) + ", " + str(measure_id) + ", " + str(ingredient_id) + ");")
                    else:
                        print("The ingredient is not conclusive!")
                else:
                    break
            connection.commit()
        else:
            break
else:
    ingredients_query = ''
    meals_query = ''
    num = 0
    if arguments.ingredients is not None:
        ingredients = arguments.ingredients.split(',')
        num = len(ingredients)
        ingredients_query += '( '
        for ing in ingredients:
            ingredients_query += "ingredient_name='" + ing + "' or "
        ingredients_query = ingredients_query[:-4] + ")"

    if arguments.meals is not None:
        if arguments.ingredients is not None:
            meals_query += ' And '
        meals_query += '( '
        meals = arguments.meals.split(',')
        for m in meals:
            meals_query += "meal_name='" + m + "' or "
        meals_query = meals_query[:-4] + ")"

    result = cursor.execute("""Select r.recipe_id, recipe_name from recipes r
                                inner join quantity q on r.recipe_id = q.recipe_id
                                inner join ingredients i on q.ingredient_id = i.ingredient_id
                                inner join serve s on s.recipe_id = r.recipe_id
                                inner join meals m on m.meal_id = s.meal_id
                                where """ + ingredients_query + meals_query + """
                                group by r.recipe_id, recipe_name
                                having count(Distinct i.ingredient_id)=""" + str(num))
    all_rows = result.fetchall()
    if len(all_rows) > 0:
        recipes = []
        for elem in all_rows:
            recipes.append(elem[1])
        print("Recipes selected for you: " + ", ".join(recipes))
    else:
        print("There are no such recipes in the database.")


connection.close()

