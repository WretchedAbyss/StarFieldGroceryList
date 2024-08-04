from fasthtml.common import *
from db import *

app, rt = fast_app(live=True)
grocery_list_items = []
def add_item_to_grocery_list(name):
    """Add item to grocery list if it doesn't exist"""
    if name not in grocery_list_items:
        grocery_list_items.append(name)

async def get_grocery_list_items():
    """Return the list of items currently in the grocery list"""
    return grocery_list_items
def remove_item_from_grocery_list(name):
    """Remove item from grocery list if it exists"""
    if name in grocery_list_items:
        grocery_list_items.remove(name)

def mk_input(): return Input(type='text', placeholder='Search', id='query', hx_swap_oob='true', hx_get='/suggest', hx_trigger='keyup changed delay:500ms', hx_target='#suggestions')

@rt("/")
def get():
    #groceries.insert(Grocery(title='Toothpicks',quantity = 1))
    search = Form(
    Group(
        mk_input(),
        ),
        hx_post='/', target_id= 'results'
    )
    lists = Div(
        Div(
            Ul(style="list-style-type: none; padding: 0; margin: 0;"), 
            style="float: left; width: 50%;",
            id = 'results'
        ),
        Div(
            Ul(style="list-style-type: none; padding: 0; margin: 0;"), 
            style="float: left; width: 50%;",
            id = 'GroceryList'
        ),
        style="width: 100%; overflow: hidden;"
    )
    suggestions = Div(id='suggestions', style="list-style-type: none; padding: 0; margin: 0;")

    return Titled("StarField Grocery list",Card(Div(search, suggestions)),Card(lists))

@rt('/', methods=['POST'])
async def post(request):
    #print(dir(request))
        # Await the form method to retrieve the form data
    form_data = await request.form()
    
    # Access the form data like a dictionary
    query = form_data['query'] 
    #print("Captured Query:", query)
    if query:
        results = search_names(query)
        results_html = Ul(*
        [Li(A(name,hx_get=f'/add_to_grocery_list?name={name}', hx_target="#GroceryList", hx_swap="beforeend" 
            )) for name in results],
        style="list-style-type: none; padding: 0; margin: 0;")
        return results_html,mk_input()  # Return only the list part
    else:
        return "No query provided.",mk_input()

@rt('/suggest', methods=['GET'])
async def suggest(request):
    query = request.query_params.get('query')
    print("Captured Query:", query)
    
    if query:
        # Dummy search function; replace with your actual search logic
        results = search_names(query)
        results_html = results_html = Ul(
            *[Li(A(name, hx_get=f'/add_to_grocery_list?name={name}', hx_target="#GroceryList", hx_swap="beforeend"), 
                style="list-style-type: none; padding: 0; margin: 0;") for name in results], 
            style="list-style-type: none; padding: 0; margin: 0;"
        )
        return  results_html
    else:
        return ""

@rt('/add_to_grocery_list', methods=['GET'])
async def add_to_grocery_list(request):
    name = request.query_params.get('name')
    if name:
        items = await get_grocery_list_items()
        if name not in items:
            add_item_to_grocery_list(name)
            print(grocery_list_items)
            list_item = Li(
                Div(
                    Div(name, style="flex: 1; padding-right: 10px; text-align: right;"),
                    Input(
                    type='number', value='1', min='0', name=f'quantity-{name}', style="width: 60px;", 
                    hx_post=f'/update_quantity?name={name}', hx_trigger='change', 
                    hx_target=f'#item-{name.replace(" ", "-")}', hx_swap='outerHTML'
                    ),  # Set a fixed width for the input field
                    style="display: flex; justify-content: space-between; align-items: center; width: 100%;"
                ),
                id=f'item-{name.replace(" ", "-")}',
                style="list-style-type: none; padding: 0; margin: 0;"  # Remove bullet points from the list item
            )
            return list_item
        return None
    else:
        return "No item selected."

@rt('/update_quantity', methods=['POST'])
async def update_quantity(request):
    name = request.query_params.get('name')
    form_data = await request.form()
    quantity = int(form_data.get(f'quantity-{name}', 1))
    if quantity < 1:
        remove_item_from_grocery_list(name)
        return ""
    else:
        list_item = Li(
            Div(
                Div(name, style="flex: 1; padding-right: 10px; text-align: right;"),
                Input(
                    type='number', value=str(quantity), min='0', name=f'quantity-{name}', style="width: 60px;", 
                    hx_post=f'/update_quantity?name={name}', hx_trigger='change', 
                    hx_target=f'#item-{name.replace(" ", "-")}', hx_swap='outerHTML'
                ),  # Maintain fixed width for the input field
                style="display: flex; justify-content: space-between; align-items: center; width: 100%;"
            ),
            id=f'item-{name.replace(" ", "-")}',
            style="list-style-type: none; padding: 0; margin: 0;"  # Remove bullet points from the list item
        )
        return list_item