from fastui import components as c
from fastui.events import GoToEvent

def page_indexation(
    total_elems: int, limit: int, offset: int, num_visible_pages: int
):
    # Calculate total number of pages
    total_pages = (total_elems + limit - 1) // limit
    
    # Calculate current page number
    current_page = (offset // limit) + 1

    # Determine start and end page numbers
    if total_elems <= num_visible_pages:
        start_page = 1
        end_page = total_pages
    elif current_page <= num_visible_pages // 2 + 1:
        start_page = 1
        end_page = num_visible_pages
    elif current_page >= total_pages - num_visible_pages // 2:
        start_page = total_pages - num_visible_pages + 1
        end_page = total_pages
    else:
        start_page = current_page - num_visible_pages // 2
        end_page = current_page + num_visible_pages // 2

    return start_page, end_page, total_pages


def generate_pagination_buttons(
    total_elements: int, limit: int, offset: int, num_visible_pages: int
):
    start_page, end_page, total_pages = page_indexation(
        total_elems=total_elements, 
        limit=limit, 
        offset=offset, 
        num_visible_pages=num_visible_pages
    )

    # Generate page number links/buttons
    page_buttons = []

    # Function to add page link/button
    def add_page_button(page_number: int, url: str):
        page_number=str(page_number).rjust(len(str(total_pages)), ' ')
        page_buttons.append(
            c.Button(
                text=page_number,
                on_click=GoToEvent(url=url),
                class_name="page-button"
            )
        )

    # Function to add ellipsis link/button
    def add_ellipsis_button(url: str):
        page_buttons.append(
            c.Button(
                text='...', 
                on_click=GoToEvent(url=url), 
                class_name="ellipsis-button"
            )
        )

    # Add ellipsis and first page link if necessary
    if start_page > 1:
        add_page_button(1, f'/?offset=0&limit={limit}')
        if start_page > 2:
            add_ellipsis_button(
                f'/?offset={max(offset - num_visible_pages * limit, 0)}&limit={limit}'
            )

    # Add page links/buttons for the visible range
    for p in range(start_page, end_page + 1):
        add_page_button(p, f'/?offset={(p - 1) * limit}&limit={limit}')

    # Add ellipsis and last page link if necessary
    if end_page < total_pages:
        if end_page < total_pages - 1:
            add_ellipsis_button(f'/?offset={(end_page + 2) * limit}&limit={limit}')
        
        add_page_button(total_pages, f'/?offset={(total_pages - 1) * limit}&limit={limit}')

    return page_buttons