#!/usr/bin/env python
# -*- coding: utf-8 -*-
#   thoth-dependency-monkey
#   Copyright(C) 2018 Christoph Görn
#
#   This program is free software: you can redistribute it and / or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Thoth: Dependency Monkey API"""


class EcosystemNotSupportedError(Exception):
    """Exception raised if a Ecosystem is not supported.

    Attributes:
        name -- name of the ecosystem
    """

    def __init__(self, name):
        self.name = name
        self.message = "Ecosystem {} is not supported".format(name)

    def str(self):
        return self.message


ECOSYSTEM = ['pypi']
