# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': "Auto Add Task Follower",
    'version': "11.0.1.0.1",
    'author': "Port Cities Ltd",
    'website': "http://www.portcities.net",
    'category': "Project",
    'summary': "Add task reviewer as a follower",
    'description': """
Author:\n
    Masoud Ananahad\n
\n
When a task have reviewer, this reviewer will add
to the followers automatically as well.\n
\n
v.1.0.1
migrate to v11 and pylint improve by WS
    """,
    'data': [],
    'depends': [
        'base',
        'project',
    ],
    'js': [],
    'qweb': [],
    'images': [],
    'demo_xml': [],
    'test': [],
    'application': False,
    'installable': True,
    'auto_install': False,
}
