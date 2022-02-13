# Tandoor KptnCook Importer

This script imports recipes from the great app [KptnCook](https://www.kptncook.com/) to the [Tandoor cookbook](https://tandoor.dev/).
The script is based on my previous [research](https://medium.com/analytics-vidhya/reversing-and-analyzing-the-cooking-app-kptncook-my-recipe-collection-5b5b04e5a085) of the KptnCook application.

## How to use

```
Usage: main.py [OPTIONS] HOST API_KEY SRC

  Request a recipe (<SRC>) from KptnCook and import it into the Tandoor
  cookbook on <HOST> using the Tandoor <API_KEY>. <SRC> can either be the
  recipe id or the shared recipe url.

Options:
  --language [de|en]         choose the language
  --units [metric|imperial]  choose the untis
  --with_time BOOLEAN        import time into recipes
  --help                     Show this message and exit.
```

Either the KptnCook recipe sharing URL can be used to parse a recipe:
```
    python main.py https://my-tandoor-server.de/ TANDOOR_API_KEY https://sharing.kptncook.com/IJ7UqFSDCnb
```

Or the recipe id can be used:
```
    python main.py https://my-tandoor-server.de/ TANDOOR_API_KEY 4ec60c5d
```
