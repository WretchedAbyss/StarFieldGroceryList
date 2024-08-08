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

# Route for rendering the tree structure
@rt('/tree_structure', methods=['GET'])
async def tree_structure():
    items = await get_grocery_list_items()
    if not items:
        return ""

    # Recursive function to build the tree for an item
    def create_tree(item, multiplier=1):
        tree_items = []

        organic = organicRequire(item)
        inorganic = inorganicRequire(item)
        manufactured = manufacturedRequire(item)

        if organic:
            organic_list = [Div(AX(f"{req} (x{qty * multiplier})", href="#", cls="organic"), cls="Child") for req, qty in organic.items()]
            tree_items.extend(organic_list)

        if inorganic:
            inorganic_list = [Div(AX(f"{req} (x{qty * multiplier})", href="#", cls="inorganic"), cls="Child") for req, qty in inorganic.items()]
            tree_items.extend(inorganic_list)

        if manufactured:
            manufactured_items = []
            for req, qty in manufactured.items():
                sub_tree = create_tree(req, multiplier * qty)
                manufactured_items.append(
                    Div(
                        AX(f"{req} (x{qty * multiplier})", href="#", cls="manufactured"),
                        Div(*sub_tree, cls="Parent") if sub_tree else "",
                        cls="Child"
                    )
                )
            tree_items.extend(manufactured_items)

        return tree_items if tree_items else []

    # Build the tree structure for all items in the grocery list
    tree_structure = [
        Div(
            f"{item} (x{qty})",
            Div(*create_tree(item, qty) or [], cls="Parent"),
            cls="Main"
        )
        for item, qty in items.items()
    ]

    # Custom CSS for styling the tree with "L" shaped connectors
    tree_style = Style("""
        .Tree .Main {
            font-weight: bold;
            margin-bottom: 10px;
        }
        .Tree .Parent {
            padding-left: 20px;
            margin-top: 5px;
            position: relative;
        }
        .Tree .Child {
            position: relative;
            padding-left: 20px;
        }
        .Tree .Child::before {
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            width: 8px;
            height: 1em;
            border-bottom: 2px solid white; /* Horizontal line */
            border-left: 2px solid white; /* Vertical line */
        }
        .Tree .Child::after {
            content: "";
            position: absolute;
            bottom: 0px;
            left: 0px;
            width: 8px;
            height: 100%;
            border-left: 2px solid white; /* Vertical line */
            }
        .Tree .Child:last-child::after{
            border-left: none;
        }
        .Tree .Parent:last-child::before {
            border-left: none;
        }
        .Tree .Parent::before {
            content: "";
            position: absolute;
            top: 0;
            bottom: 0;
            left: 0;
            border-left: 2px solid white; /* Vertical line connecting parents */
        }
        .Tree .organic {
            background-color: lightgreen !important;
            border-radius: 3px;
            padding: 2px 5px;
        }
        .Tree .inorganic {
            background-color: lightcoral !important;
            border-radius: 3px;
            padding: 2px 5px;
        }
        .Tree .manufactured {
            background-color: lightblue;
            border-radius: 3px;
            padding: 2px 5px;
        }
    """)

    return Div(tree_style, Div(*tree_structure, cls="Tree"), cls="container")

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
        Div(
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
            cls="Child"
        )
        for name, quantity in items.items()
    ]

    lists = Div(
        Div(
            Div(*list_elements, cls="Parent"), 
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

def mk_input(): return Input(type='text', placeholder='Search', id='query', hx_swap_oob='true', hx_get='/suggest', hx_trigger='keyup changed delay:500ms', hx_target='#suggestions')

@rt('/suggest', methods=['GET'])
async def suggest(request):
    query = request.query_params.get('query')
    if query:
        results = search_names(query)
        results_html = Div(
            *[Div(A(name, hx_get=f'/add_to_grocery_list?name={name}', hx_target="#GroceryList", hx_swap="beforeend"), cls="Child") for name in results],
            cls="Parent"
        )
        return results_html
    else:
        return ""

@rt('/add_to_grocery_list', methods=['GET'])
async def add_to_grocery_list(request):
    name = request.query_params.get('name')
    if name:
        items = await get_grocery_list_items()
        if name not in items:
            add_item_to_grocery_list(name, 1)
            list_item = Div(
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
                cls="Child"
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
        list_item = Div(
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
            cls="Child"
        )
        # Update the tree structure after updating quantity
        return list_item, Script("htmx.ajax('GET', '/tree_structure', {target: '#tree-structure'})")
