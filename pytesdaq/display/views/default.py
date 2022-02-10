from pyramid.view import (
    view_config,
    view_defaults
    )

from pytesdaq.display import db
from pytesdaq.display.series import *

server = db.MySQLCore()


@view_defaults(renderer='../templates/home.mako')
class MainViews:
    def __init__(self, request):
        self.request = request

    @view_config(route_name='home', renderer='../templates/home.mako')
    def home(self):
        return {'name': 'Home View'}

    server.connect_test()

    serieslist = server.query('series')
    grouplist = server.query('groups')

    server.disconnect()


    @view_config(route_name='series_test', renderer='../templates/series_test.mako')
    def series_test(self):

        def search(dic):
            return dic['series_num']

        serieslist = MainViews.serieslist
        serieslist.sort(key=search)
        return {'name': 'Series_Test', 'series': serieslist}

    @view_config(route_name='series_info', renderer='../templates/series_info.mako')
    def series_info(self):

        group_name = self.request.matchdict['group_name']
        series_num = self.request.matchdict['series_num'] #fix if we get 'id'
        
        ind_series = next(item for item in MainViews.serieslist if item["series_num"] == int(series_num))
        finalseries = ind_series
        return {'name': str(series_num), 'this_series': finalseries}


    @view_config(route_name='group_info', renderer='../templates/group_info.mako')
    def group_info(self):

        group_name = self.request.matchdict['group_name'] 

        server.connect_test()

        serieslist = server.query('series', ['group_name', group_name])

        server.disconnect()

        ind_group = next(item for item in MainViews.grouplist if item["group_name"] == group_name)
        finalgroup = ind_group

        return {'name': str(group_name), 'this_group': ind_group, 'group_series_list': serieslist}


    @view_config(route_name='groups', renderer='../templates/group.mako')
    def groups(self):

        def search(dic):
            return dic['group_name']

        grouplist = MainViews.grouplist
        grouplist.sort(key=search)
        return {'name': 'Groups', 'grouplist': grouplist}

    



    




