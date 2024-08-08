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

# Route for rendering the tree structure
@rt('/tree_structure', methods=['GET'])
async def tree_structure():
    items = await get_grocery_list_items()
    if not items:
        return ""

    # Recursive function to build the tree for an item
    def create_tree(item, multiplier=1):
        tree_items = []

        # Get the different types of requirements
        organic = organicRequire(item)
        inorganic = inorganicRequire(item)
        manufactured = manufacturedRequire(item)

        # Add organic requirements with green background on text
        if organic:
            organic_list = [Li(Span(f"{req} (x{qty * multiplier})", cls="organic")) for req, qty in organic.items()]
            tree_items.extend(organic_list)

        # Add inorganic requirements with red background on text
        if inorganic:
            inorganic_list = [Li(Span(f"{req} (x{qty * multiplier})", cls="inorganic")) for req, qty in inorganic.items()]
            tree_items.extend(inorganic_list)

        # Add manufactured requirements recursively with blue background on text
        if manufactured:
            manufactured_items = []
            for req, qty in manufactured.items():
                sub_tree = create_tree(req, multiplier * qty)
                if sub_tree:
                    manufactured_items.append(
                        Details(Summary(Span(f"{req} (x{qty * multiplier})", cls="manufactured")), Ul(*sub_tree), open=True, cls="manufactured")
                    )
                else:
                    manufactured_items.append(Li(Span(f"{req} (x{qty * multiplier})", cls="manufactured")))
            
            if manufactured_items:
                tree_items.extend(manufactured_items)

        return tree_items if tree_items else []

    # Build the tree structure for all items in the grocery list
    tree_structure = [
        Details(Summary(Span(f"{item} (x{qty})", cls="main-item")), Ul(*create_tree(item, qty) or []), open=True)
        for item, qty in items.items()
    ]

    # Custom CSS for styling the tree
    tree_style = Style("""
        .Tree ul summary{
            cursor: pointer;
            line-height:2em;
        }
        .Tree ul summary::marker{
            display:none;
        }
        .Tree summary::-webkit-details-marker{
            display:none;
        }
        .Tree ul li{
            position:relative;
            list-style-type: none;
        }
        .Tree li {
            margin: 0;
            padding: 0 0 0 0px;
            list-style-type: none;
            line-height: 1.5;
            position: relative;
        }
        .Tree ul li::before{
            position: absolute;
            left:-10px;
            top:0px;
            border-left:2px solid white;
            border-bottom:2px solid white;
            content:"";
            width:8px;
            height:1em;
        }
        .Tree ul li::after{
            position: absolute;
            left:-10px;
            bottom:0px;
            border-left:2px solid white;
            content:"";
            width:8px;
            height:1em;
        }
        .Tree ul li:last-child::after{
            display:none;
        }
        .Tree > ul > li:first-child::before,
        .Tree > ul > li:first-child::after {
            content: none;
            display: none;
        }
        
        .Tree details summary {
            cursor: pointer;
            margin: 0 0 0 0;
        }
        .Tree .manufactured details summary::before {
            position: relative;
            display:block;
            left:-10px;
            top:18px;
            border-left:2px solid white;
            border-bottom:2px solid white;
            content:"";
            width:8px;
            height:1em;
            
        }
        .Tree details summary::after {
            display:none;
        }
        .Tree .main-item {
            font-weight: bold;
        }
        .Tree .organic {
            background-color: lightgreen !important;
            border-radius: 3px;
        }
        .Tree .inorganic {
            background-color: lightcoral !important;
            border-radius: 3px;
        }
        .Tree .manufactured span{
            background-color: lightblue;
            border-radius: 3px;
            position: relative;
        }
    """)

    return Div(tree_style, Div(Ul(*tree_structure), cls="Tree"), cls="container")

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

def mk_input(): return Input(type='text', placeholder='Search', id='query', hx_swap_oob='true', hx_get='/suggest', hx_trigger='keyup changed delay:500ms', hx_target='#suggestions')
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