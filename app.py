from fasthtml.common import *
from utils.starcal import *

app, rt = fast_app('StarField.db', live=True)
grocery_list_items = {}
def add_item_to_grocery_list(name, quantity=1):
    
    if name in grocery_list_items:
        grocery_list_items[name] += quantity
    else:
        grocery_list_items[name] = quantity

async def get_grocery_list_items():
    """Return the list of items currently in the grocery list"""
    return grocery_list_items
def remove_item_from_grocery_list(name):
    """Remove item from grocery list if it exists"""
    if name in grocery_list_items:
        del grocery_list_items[name]
        
def list_depth(lst):
    if not isinstance(lst, list) or not lst:
        return 0
    return 1 + max(list_depth(item) for item in lst)
# Recursive function to build the tree for an item
def create_tree(item, multiplier=1):
    tree_items = []

    # Get the different types of requirements
    organic = organicRequire(item)
    inorganic = inorganicRequire(item)
    manufactured = manufacturedRequire(item)

    # Add organic requirements with green background on text
    if organic:
        organic_list = Ul(*[Li(Span(f"{req} (x{qty * multiplier})", style="background-color: green; padding: 2px; border-radius: 3px;")) for req, qty in organic.items()])
        tree_items.append(organic_list)

    # Add inorganic requirements with red background on text
    if inorganic:
        inorganic_list = Ul(*[Li(Span(f"{req} (x{qty * multiplier})", style="background-color: red; padding: 2px; border-radius: 3px;")) for req, qty in inorganic.items()])
        tree_items.append(inorganic_list)

    # Add manufactured requirements recursively with blue background on text
    if manufactured:
        manufactured_items = []
        for req, qty in manufactured.items():
            sub_tree = create_tree(req, multiplier * qty)
            if sub_tree:
                manufactured_items.append(Li(Span(f"{req} (x{qty * multiplier})", style="background-color: blue; padding: 2px; border-radius: 3px;"), Ul(*sub_tree)))
            else:
                manufactured_items.append(Li(Span(f"{req} (x{qty * multiplier})", style="background-color: blue; padding: 2px; border-radius: 3px;")))

        if manufactured_items:
            tree_items.append(Ul(*manufactured_items))

    # Sort the tree items by the depth of their sublists
    tree_items = sorted(tree_items, key=list_depth)

    return tree_items if tree_items else None

# Route for rendering the tree structure
@rt('/tree_structure', methods=['GET'])
async def tree_structure():
    items = await get_grocery_list_items()
    if not items:
        return ""

    # Build the tree structure for all items in the grocery list, passing the quantity as a multiplier
    tree_structure = Ul(
        *[Li(f"{item} (x{qty})", Ul(*create_tree(item, qty) or [])) for item, qty in items.items()]
    )
    return Div(tree_structure, cls="container")

def mk_input(): return Input(type='text', placeholder='Search', id='query', hx_swap_oob='true', hx_get='/suggest', hx_trigger='keyup changed delay:500ms', hx_target='#suggestions')

@rt("/")
async def get():
    search = Form(
        Group(
            Div(
                mk_input(),
                Div(id='suggestions', style="position: relative;"),
                style="position: relative;"
            ),
        ),
        hx_post='/', target_id='results'
    )

    items = await get_grocery_list_items()
    list_elements = [
        Li(
            Div(
                Div(name, style="flex: 1; padding-right: 10px; text-align: right;"),
                Input(
                    type='number', value=str(quantity), min='0', name=f'quantity-{name}', style="width: 60px;",
                    hx_post=f'/update_quantity?name={name}', hx_trigger='change',
                    hx_target=f'#item-{name.replace(" ", "-")}', hx_swap='outerHTML'
                ),
                style="display: flex; justify-content: space-between; align-items: center; width: 100%;"
            ),
            id=f'item-{name.replace(" ", "-")}',
            style="list-style-type: none; padding: 0; margin: 0;"
        )
        for name, quantity in items.items()
    ]

    lists = Div(
        Div(
            Ul(*list_elements, style="list-style-type: none; padding: 0; margin: 0;"), 
            style="float: left; width: 50%;",
            id='GroceryList'
        ),
        style="width: 50%; overflow: hidden;"
    )

    # Placeholder div for tree structure
    tree_div = Div(id='tree-structure', hx_get='/tree_structure', hx_trigger='load')

    return Titled("StarField Grocery List"),  Div(
               Card(Div(search)),
               Card(lists),
               tree_div
           )

@rt('/suggest', methods=['GET'])
async def suggest(request):
    query = request.query_params.get('query')
    #print("Captured Query:", query)
    if query:
        results = search_names(query)
        results_html = Ul(
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
            add_item_to_grocery_list(name, 1)
            list_item = Li(
                Div(
                    Div(name, style="flex: 1; padding-right: 10px; text-align: right;"),
                    Input(
                        type='number', value='1', min='0', name=f'quantity-{name}', style="width: 60px;",
                        hx_post=f'/update_quantity?name={name}', hx_trigger='change',
                        hx_target=f'#item-{name.replace(" ", "-")}', hx_swap='outerHTML'
                    ),
                    style="display: flex; justify-content: space-between; align-items: center; width: 100%;"
                ),
                id=f'item-{name.replace(" ", "-")}',
                style="list-style-type: none; padding: 0; margin: 0;"
            )
            # Update the tree structure after adding an item
            return list_item, Script("htmx.ajax('GET', '/tree_structure', {target: '#tree-structure'})")
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
        # Update the tree structure when the item is removed (if last item, tree will disappear)
        return "", Script("htmx.ajax('GET', '/tree_structure', {target: '#tree-structure'})")
    else:
        grocery_list_items[name] = quantity
        list_item = Li(
            Div(
                Div(name, style="flex: 1; padding-right: 10px; text-align: right;"),
                Input(
                    type='number', value=str(quantity), min='0', name=f'quantity-{name}', style="width: 60px;",
                    hx_post=f'/update_quantity?name={name}', hx_trigger='change',
                    hx_target=f'#item-{name.replace(" ", "-")}', hx_swap='outerHTML'
                ),
                style="display: flex; justify-content: space-between; align-items: center; width: 100%;"
            ),
            id=f'item-{name.replace(" ", "-")}',
            style="list-style-type: none; padding: 0; margin: 0;"
        )
        # Update the tree structure after updating quantity
        return list_item, Script("htmx.ajax('GET', '/tree_structure', {target: '#tree-structure'})")