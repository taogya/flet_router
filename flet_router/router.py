import logging
import typing as typ
from urllib.parse import parse_qs, urlparse

import flet as ft
from repath import match


class Path(typ.NamedTuple):
    path: str
    func: typ.Callable[[ft.RouteChangeEvent, typ.Any], ft.View]
    clear: bool = True


class Redirect(Exception):
    def __init__(self, route: str):
        self.route = route


class Router:
    logger = logging.getLogger('flet_router')
    routes: typ.List[Path] = []
    init_route = '/'
    debug = False
    force_clear = False

    def __init__(self,
                 page: ft.Page):
        self.page = page
        self.page.on_connect = self.on_connect
        self.page.on_disconnect = self.on_disconnect
        self.page.on_route_change = self.on_route_change
        self.page.on_view_pop = self.on_view_pop

        self.logger.debug(f'__init__: session_id = {self.page.session_id}')

    def on_connect(self,
                   event: ft.ControlEvent):
        self.logger.debug(f'on_connect: {event}, session_id = {event.page.session_id}')

    def on_disconnect(self,
                      event: ft.ControlEvent):
        self.logger.debug(f'on_disconnect: {event}, session_id = {event.page.session_id}')

    def __urlparse(self,
                   route: str) -> typ.Tuple[typ.Optional[str], typ.Dict[str, typ.List[str]]]:
        try:
            parsed = urlparse(route)
            path = parsed.path.rstrip('/') or '/'
            query = parse_qs(parsed.query)
            return path, query
        except TypeError:
            return None, {}

    def on_route_change(self,
                        event: ft.RouteChangeEvent):
        self.logger.debug(f'on_route_change: {event}, stack views = {len(self.page.views)}')

        # TODO: クエリパラメータを含む場合に、正しくマッチングできるようにする対応
        event_path, event_query = self.__urlparse(event.route)
        self.logger.debug(f'on_route_change: event_path = {event_path}, event_query = {event_query}')

        # TODO: Web で画面積み上げ状態でリロード時に、今の画面が再積み上げされてしまう問題の対応
        # TODO: クエリパラメータはurlencodeを使用すると、空のデータの場合、?test= となる
        # TODO: リロードした際、そのクエリパラメータを受け取った画面のrouteは?test となってしまうためこの処理をしている
        current_path, current_query = self.__urlparse(self.page.views[-1].route)
        self.logger.debug(f'on_route_change: current_path = {current_path}, current_query = {current_query}')
        if event_path == current_path and event_query == current_query:
            self.logger.debug('on_route_change: route is the same')
            return

        # TODO: ルートのマッチング処理
        matched_list = map(lambda route: match(route.path, event_path),
                           self.routes)
        route, matched = next(filter(lambda x: x[1],
                                     zip(self.routes, matched_list)),
                              (Path(None, self.response_404, False), {}))
        kwargs = matched and matched.groupdict()
        self.logger.debug(f'on_route_change: route = {route}, matched = {matched}, kwargs = {kwargs}')

        try:
            view = route.func(event, **kwargs)
            if route.clear:
                self.page.views.clear()
                self.logger.debug('on_route_change: clear views')
        except Redirect as ex:
            # TODO: 画面積み上げをクリアするかは、リダイレクト先で決定する
            self.page.go(ex.route)
            self.logger.debug(f'on_route_change: redirect to {ex.route}')
            return
        except BaseException:
            # TODO: エラー時は画面を積み上げる
            self.logger.exception('on_route_change: error')
            view = self.response_500(event)

        if self.force_clear:
            self.page.views.clear()
            self.logger.debug('on_route_change: force clear views')

        self.page.views.append(view)
        self.page.update()
        self.logger.debug(f'on_route_change: added = {view}, stack views = {len(self.page.views)}')

    def on_view_pop(self,
                    event: ft.ViewPopEvent):
        self.logger.debug(f'on_view_pop: {event}')
        pop_view = self.page.views.pop()
        # TODO: Web 実行時かつ、force_clear 有効時にリロードを行い、戻るボタンを押すと積み上げ画面がないのに on_view_pop が呼ばれる問題の対応
        go_view = self.page.views[-1] if self.page.views else pop_view

        self.page.go(go_view.route)
        self.logger.debug(f'on_view_pop: pop_view = {pop_view}, go_view = {go_view}')

    def response_404(self,
                     event: ft.RouteChangeEvent) -> ft.View:
        self.logger.debug(f'response_404: {event}')
        return ft.View(
            appbar=ft.AppBar(title=ft.Text('404 not found')),
            padding=20)

    def response_500(self,
                     event: ft.RouteChangeEvent) -> ft.View:
        self.logger.debug(f'response_500: {event}')
        view = ft.View(
            appbar=ft.AppBar(title=ft.Text('500 internal server error')),
            padding=20)
        if self.debug:
            import traceback
            view.controls.append(ft.Text(traceback.format_exc()))
        return view

    @ classmethod
    def add_route(cls,
                  path: str,
                  func: typ.Callable[[ft.RouteChangeEvent, typ.Any], ft.Control],
                  clear: bool = True):
        cls.routes.append(Path(path, func, clear))

    @ classmethod
    def route(cls,
              path: str,
              clear: bool = True):
        def decorator(func: typ.Callable[[ft.RouteChangeEvent, typ.Any], ft.Control]):
            cls.add_route(path, func, clear)
            return func
        return decorator

    @ classmethod
    def config(cls,
               debug: bool = False,
               logger: logging.Logger = None,
               force_clear: bool = False) -> 'Router':
        cls.debug = debug
        cls.logger = logger or cls.logger
        cls.force_clear = force_clear

        return cls

    @ classmethod
    def main(cls,
             page: ft.Page):
        cls(page).page.go(cls.init_route)
