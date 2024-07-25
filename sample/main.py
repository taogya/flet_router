
from logging.config import dictConfig

import flet as ft

from flet_router import Path, Redirect, Router

dictConfig({
    'version': 1,
    'formatters': {
        'default': {
            'format': '%(asctime)s,%(name)s,%(levelname)s,%(message)s',
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
        }
    },
    'loggers': {
        'flet_router': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'main': {
            'handlers': ['console'],
            'level': 'DEBUG',
        }
    }
})


def home(event: ft.RouteChangeEvent) -> ft.View:
    return ft.View(
        route=event.route,
        appbar=ft.AppBar(title=ft.Text('Home')),
        controls=[
            ft.Text('Hello, home!', size=24, weight=ft.FontWeight.BOLD),
            ft.ElevatedButton('Go to class view', on_click=lambda e: e.page.go('/class/2')),
        ],
        padding=20)


class ClassView(ft.View):
    def __init__(self, event: ft.RouteChangeEvent, id: str = None):
        super().__init__(route=event.route)
        self.appbar = ft.AppBar(title=ft.Text('My View'))
        self.controls = [
            ft.Text(f'Hello, class view! id = {id}', size=24, weight=ft.FontWeight.BOLD),
            ft.ElevatedButton('Go to decorator view', on_click=lambda e: e.page.go('/decorator?query=1')),
        ]
        self.padding = 20


class MyRouter(Router):
    routes = [
        Path('/', home),
        Path('/class/:id', ClassView, False)
    ]


@ MyRouter.route('/decorator', clear=False)
def decorator(event: ft.RouteChangeEvent) -> ft.View:
    return ft.View(
        route=event.route,
        appbar=ft.AppBar(title=ft.Text('Decorator')),
        controls=[
            ft.Text('Hello, decorator view!', size=24, weight=ft.FontWeight.BOLD),
            ft.Text(f'query = {event.page.query.to_dict}'),
            ft.ElevatedButton('Go to add route view', on_click=lambda e: e.page.go('/add_route')),
        ],
        padding=20)


def add_route(event: ft.RouteChangeEvent) -> ft.View:
    return ft.View(
        route=event.route,
        appbar=ft.AppBar(title=ft.Text('Add Route')),
        controls=[
            ft.Text('Hello, add route view!', size=24, weight=ft.FontWeight.BOLD),
            ft.ElevatedButton('Go to not found', on_click=lambda e: e.page.go('/poyoyo')),
            ft.ElevatedButton('Go to redirect', on_click=lambda e: e.page.go('/redirect')),
            ft.ElevatedButton('Go to error', on_click=lambda e: e.page.go('/error')),
        ],
        padding=20)


def redirect(event: ft.RouteChangeEvent) -> ft.View:
    raise Redirect('/redirect')


def error(event: ft.RouteChangeEvent) -> ft.View:
    raise Exception('error')


MyRouter.add_route('/add_route', add_route, clear=False)
MyRouter.add_route('/redirect', redirect, clear=False)
MyRouter.add_route('/error', error, clear=False)

if __name__ == '__main__':
    import logging

    ft.app(MyRouter.config(debug=True,
                           logger=logging.getLogger('main'),
                           force_clear=True).main,
           view=ft.AppView.WEB_BROWSER,
           port=8000)
    # ft.app(MyRouter.main)
