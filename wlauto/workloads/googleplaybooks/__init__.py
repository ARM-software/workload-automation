#    Copyright 2014-2016 ARM Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from wlauto import AndroidUxPerfWorkload, Parameter
from wlauto.exceptions import DeviceError


class Googleplaybooks(AndroidUxPerfWorkload):

    name = 'googleplaybooks'
    package = 'com.google.android.apps.books'
    min_apk_verson = '3.9.37'
    activity = 'com.google.android.apps.books.app.BooksActivity'
    view = [package + '/com.google.android.apps.books.app.HomeActivity',
            package + '/com.android.vending/com.google.android.finsky.activities.MainActivity',
            package + '/com.google.android.apps.books.app.ReadingActivity',
            package + '/com.google.android.apps.books.app.TableOfContentsActivityLight']
    description = """
    A workload to perform standard productivity tasks with googleplaybooks.
    This workload performs various tasks, such as searching for a book title
    online, browsing through a book, adding and removing notes, word searching,
    and querying information about the book.

    Test description:
     1. Open Google Play Books application
     2. Dismisses sync operation (if applicable)
     3. Searches for a book title
     4. Adds books to library if not already present
     5. Opens 'My Library' contents
     6. Opens selected  book
     7. Gestures are performed to swipe between pages and pinch zoom in and out of a page
     8. Selects a specified chapter based on page number from the navigation view
     9. Selects a word in the centre of screen and adds a test note to the page
    10. Removes the test note from the page (clean up)
    11. Searches for the number of occurrences of a common word throughout the book
    12. Switches page styles from 'Day' to 'Night' to 'Sepia' and back to 'Day'
    13. Uses the 'About this book' facility on the currently selected book

    NOTE: This workload requires a network connection (ideally, wifi) to run
          and a Google account to be setup on the device.
    """

    parameters = [
        Parameter('search_book_title', kind=str, mandatory=False, default="Hamlet",
                  description="""
                  The book title to search for within Google Play Books archive.
                  The book must either be already in the account's library, or free to purchase.
                  """),
        Parameter('select_chapter_page_number', kind=int, mandatory=False, default=22,
                  description="""
                  The Page Number to search for within a selected book's Chapter list.
                  Note: Accepts integers only.
                  """),
        Parameter('search_word', kind=str, mandatory=False, default='the',
                  description="""
                  The word to search for within a selected book.
                  Note: Accepts single words only.
                  """),
    ]

    requires_network = True

    def validate(self):
        super(Googleplaybooks, self).validate()
        self.uiauto_params['book_title'] = self.search_book_title.replace(" ", "0space0")
        self.uiauto_params['chapter_page_number'] = self.select_chapter_page_number
        self.uiauto_params['search_word'] = self.search_word
