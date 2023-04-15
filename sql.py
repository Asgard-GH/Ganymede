"""
Copyright 2022 Ganymede Development

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software. Access to the software
is not to be used for malicious actions or the attempt thereof, including,
but not limited to: Circumventing security and/or moderation features of the
Discord Bot "Ganymede" (hereafter referred to as "Ganymede", "Ganymedes"),
evading automated moderation features of Ganymede, harming the performance of
Ganymede, using Ganymede in guilds that do not intend to allow you to use it
(this includes restricting your account from parts of Ganymedes features or its
entirety), gaining control of Ganymedes account.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""
"""The purpose of this file is making changes to the 'ganymede.db' database"""
import sqlite3

connection = sqlite3.connect("ganymede.db")
with connection:
    cursor = connection.cursor()
    cursor.execute(
        """CREATE TABLE Visible VALUES (G_ID int, Ca_ID int)"""
    )
    print(cursor.fetchone())
