from datetime import date
from typing import Optional
from faker import Faker  

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from fastui import FastUI, AnyComponent, prebuilt_html, components as c
from fastui.components.display import DisplayMode, DisplayLookup
from fastui.events import GoToEvent
from pydantic import BaseModel, Field

from constants import MAX_VISIBLE_PAGES
from utils import generate_pagination_buttons

app = FastAPI()

# Initialize Faker library
fake = Faker()

class UserCursor(BaseModel):
    id: int
    prev_id: Optional[int] = None
    next_id: Optional[int] = None

class UserDetail(BaseModel):
    id: int
    name: str
    dob: date = Field(title='Date of Birth')
    email: str
    phone: str
    address: str
    city: str
    state: str
    country: str
    zip_code: str

# Given a model, generate a DisplayLookup for each field with respective 
# type and title. Provide on_click event mapping to the URL for desired fields
def generate_display_lookups(
    model: BaseModel, 
    on_click: dict[str, str] = {}
) -> list[DisplayLookup]:
    lookups = []
    for field in model.__fields__.keys():
        title = model.__fields__[field].title

        if model.__fields__[field].annotation == date:
            mode = DisplayMode.date
            lookup = DisplayLookup(field=field, title=title, mode=mode)
        else:
            lookup = DisplayLookup(field=field, title=title)

        if field in on_click:
            lookup.on_click = GoToEvent(url=on_click[field])
        lookups.append(lookup)
    return lookups


# Generate random users
# Number of random users to generate
def generate_users(n: int) -> list[UserDetail]:  
    users = []
    users_cursor = {}
    for i in range(n):
        name = fake.name()
        dob = fake.date_of_birth(minimum_age=18, maximum_age=80)
        user = UserDetail(
            id=i,
            name=name,
            dob=dob,
            email=fake.email(),
            phone=fake.phone_number(),
            address=fake.street_address(),
            city=fake.city(),
            state=fake.state(),
            country=fake.country(),
            zip_code=fake.zipcode()
        )
        users.append(user)
        id_ = user.id
        users_cursor[id_] = UserCursor(id=id_)
        
        # Set up the doubly linked list
        if i == 0:
            users_cursor[id_].prev_id = users[len(users) - 1].id
        if i > 0:
            users_cursor[id_].prev_id = users[i-1].id
        
        if i < len(users) - 1:
            users_cursor[id_].next_id = users[i+1].id
        if i == len(users) - 1:
            users_cursor[id_].next_id = users[0].id    

    return users, users_cursor

def users_lookup() -> dict[int, UserDetail]:
    users, _ = generate_users(100)
    return {user.id: user for user in users}

def users_cursor_lookup() -> dict[int, UserCursor]:
    _, users_cursor = generate_users(100)
    return users_cursor

def users_list() -> list[UserDetail]:
    return list(users_lookup().values())

users = users_list()
users_cursor = users_cursor_lookup()

# Endpoint for users table with pagination
@app.get("/users", response_model=FastUI, response_model_exclude_none=True)
def users_table(
    limit: Optional[int] = Query(10, ge=1, le=len(users)), 
    offset: int = Query(0, ge=0)
) -> list[AnyComponent]:
    """
    Show a table of users with pagination.
    """
    # Paginate users based on limit and offset
    paginated_users = users[offset:offset + limit]
    
    page_buttons=generate_pagination_buttons(
        total_elements=len(users), limit=limit, offset=offset,
        num_visible_pages=MAX_VISIBLE_PAGES
    )

    user_lookup_list=generate_display_lookups(
        UserDetail, on_click={'name': '/user/{id}/'}
    )

    table_msg=f"Displaying users {offset + 1} to {min(offset + limit, len(users))} of {len(users)}"
    components_ = [
        c.Heading(text='Users', level=2),
        c.Table(data=paginated_users, columns=user_lookup_list),
        c.Text(text=table_msg),
        c.Div(components=page_buttons, class_name="pagination")
    ]
    
    pages_ = [ c.Page(components=components_), ]

    return pages_

@app.get("/users/{user_id}/", response_model=FastUI, response_model_exclude_none=True)
def user_profile(user_id: int) -> list[AnyComponent]:
    """
    User profile page, the frontend will fetch this when the user visits `/user/{id}/`.
    """
    try:
        user_cursor = next(u for u in users_cursor.values() if u.id == user_id)
    except StopIteration:
        raise HTTPException(status_code=404, detail="User not found")
    
    user = users_lookup()[user_id]

    components_ = [
        c.Button(text='< Back to Users', on_click=GoToEvent(url='/')),
        c.Heading(text=user.name, level=2),
        c.Details(data=user),
    ]
    
    # Add the "Previous" button if there is a previous user
    if user_cursor.prev_id:
        button=c.Button(
            text='<< Previous', on_click=GoToEvent(url=f'/users/{user_cursor.prev_id}/')
        )
        components_.append(button)
    
    # Add the "Next" button if there is a next user
    if user_cursor.next_id:
        button=c.Button(
            text='Next >>', on_click=GoToEvent(url=f'/users/{user_cursor.next_id}/')
        )
        
        components_.append(button)
    
    page_ = c.Page(components=components_)
    
    return [page_]

# HTML landing page
@app.get('/{path:path}')
async def html_landing() -> HTMLResponse:
    """Simple HTML page which serves the React app, comes last as it matches all paths."""
    return HTMLResponse(prebuilt_html(title='FastUI Demo'))


    
    