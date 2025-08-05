from typing import Literal
import re
from random import choice
from unicodedata import normalize

from playwright.sync_api import (
    sync_playwright,
    Page,
    Browser,
    Locator
)

from .logger import Logger
from .constants import FW, KEYBOARD_IDS, URLS


class Termo:
    def __init__(
        self,
        browser: Literal["firefox", "chromium"] = "firefox",
        headless: bool = True,
        logging: bool = False
    ) -> None:
        self._browser: Literal['firefox', 'chromium'] = browser
        self._headless: bool = headless
        self._logging = Logger(
            config={
                "message": logging,
                "success": logging,
                "var": logging,
                "background": logging,
                "error": logging,
                "warning": logging
            }
        )

        # Default info
        self._keyboard_ids: dict[str, str] = KEYBOARD_IDS
                
        # Each page constants
        self.urls: dict[Literal['termo', 'dueto', 'quarteto'], str] = URLS
        self._max_boards: dict[Literal['termo', 'dueto', 'quarteto'], int] = {
            "termo": 1,
            "dueto": 2,
            "quarteto": 4,
        }
        self._max_attempts: dict[Literal['termo', 'dueto', 'quarteto'], int] = {
            "termo": 6,
            "dueto": 7,
            "quarteto": 9,
        }

    def termo(self, *, __page: Page | None = None) -> tuple[str]:
        """
        return: Return the solved words for the Termo game.
        """
        return self._execute(page=__page, site="termo")

    def dueto(self, *, __page: Page | None = None) -> tuple[str]:
        """
        return: Return the solved words for the Dueto game.
        """
        return self._execute(page=__page, site="dueto")

    def quarteto(self, *, __page: Page | None = None) -> tuple[str]:
        """
        return: Return the solved words for the Quarteto game.
        """
        return self._execute(page=__page, site="quarteto")

    def all(self) -> list[tuple[str], tuple[str], tuple[str]]:
        """
        return: Return the solved words for all the games.
        """
        return [self.termo(), self.dueto(), self.quarteto()]

    def _execute(
        self,
        site: Literal["termo", "dueto", "quarteto"],
        page: Page | None = None,
        word_list: list[str] = FW,
        first_word: str = "areio"
    ) -> tuple[str]:
        self._logging.message("Starting " + site + " game")

        # Starting the browser and setup the page
        with sync_playwright() as playwright:
            if page is None:
                browser: Browser = (
                    playwright.firefox.launch(headless=self._headless)
                    if self._browser == "firefox"
                    else playwright.chromium.launch(headless=self._headless)
                )
                page: Page = browser.new_page()

            page.goto(self.urls[site])
            page.mouse.click(0, 0)

            # Setting up utils variables
            possible_words: list[str] = word_list
            words_results: tuple[str] = ()
            word: str = first_word
            last_row: int = 0
            
            # Solving the game
            for board in range(self._max_boards[site]):
                self._logging.message("Starting board " + str(board+1) + " of " + str(self._max_boards[site]))
                # Setting up the board
                board_element: Locator = page.locator("#hold").nth(board)

                # If it's not the first board, we need to make a new word list for the new board
                # beacause the words are different for each board
                if board != 0:
                    word, possible_words = self._make_new_word_list(board_element=board_element, max_row=last_row)

                # Solving the board
                for i in range(last_row, self._max_attempts[site]):
                    self._try_word(page, word)
                    last_row += 1
                    letter_results: dict[str, tuple[str, str]] = self._get_color(board_element, row=i)

                    # Validate if the word is correct
                    if all(letter_results[j][1] == "green" for j in letter_results.keys()):
                        self._logging.message("Word of board " + str(board+1) + " of " + str(self._max_boards[site]) + " found: ", end="")
                        self._logging.success(word)
                        words_results = words_results + (word, )
                        break

                    else:
                        # Filter the list of possible words based on the results
                        word, possible_words = self._filter_words(letter_results, possible_words)
            
        if (site == "termo" and len(words_results) < 1) or (site == "dueto" and len(words_results) < 2) or (site == "quarteto" and len(words_results) < 4):
            self._logging.error("No word found for " + site + " game, trying again")

            # Here i use recursion to try again with the same word list when the word is not found
            if site == "termo":
                words_results = self._execute(site=site, word_list=possible_words, first_word=choice(possible_words))
            else:
                words_results = self._execute(site=site)

        return words_results

    def _try_word(self, page: Page, word: str) -> None:
        self._logging.message("Trying word: " + word)
        for letter in word:
            page.locator(self._keyboard_ids[letter]).click()

        page.locator(self._keyboard_ids["enter"]).click()
        page.wait_for_timeout(1400)

    def _filter_words(self, letter_results: dict[int, tuple[str, Literal["green", "yellow", "black"]]], possible_words: list[str]) -> tuple[str, list[str]]:
        def find_missing(input_list: list[int]) -> list[int]:
            return sorted(list({0, 1, 2, 3, 4} - set(input_list)))

        filtered_words: list[str] = possible_words
        green_pos: list[int] = []
        yellow_pos: list[str] = []
        yellow_letters: list[str] = []

        for i in letter_results.keys():
            if letter_results[i][1] == "green":
                filtered_words = [word for word in filtered_words if word[i] == letter_results[i][0]]
                green_pos.append(i)
        
        for i in letter_results.keys():
            if letter_results[i][1] == "yellow":
                filtered_words = [word for word in filtered_words if letter_results[i][0] not in word[i] and letter_results[i][0] in [word[pos] for pos in find_missing(green_pos)]]
                yellow_pos.append(i)
                yellow_letters.append(letter_results[i][0])

        for i in letter_results.keys():
            if letter_results[i][1] == "black":
                filtered_words = [word for word in filtered_words if letter_results[i][0] not in [word[pos] for pos in find_missing(green_pos + yellow_pos)] and (bool(set(word) & set(yellow_letters)) if yellow_letters else True)]

        self._logging.var(f"Possible words: {len(possible_words)} | Filtered words: {len(filtered_words)}")
        return choice(filtered_words), filtered_words

    def _make_new_word_list(self, board_element: Locator, max_row: int) -> tuple[str, list[str]]:
        filters: list[dict[str, tuple[str, str]]] = []
        for i in range(max_row):
            b: dict[str, tuple[str, str]] = self._get_color(board_element, row=i)
            filters.append(b)

        new_list: list[str] = FW
        for i in range(max_row):
            _, new_list = self._filter_words(letter_results=filters[i], possible_words=new_list)

        return choice(new_list), new_list

    def _get_color(self, board_div_element: Locator, row: int) -> dict[str, tuple[str, Literal["green", "yellow", "black"]]]:
        wc_row: Locator = board_div_element.locator("wc-row").nth(row)
        divs: list[Locator] = wc_row.locator("div").all()
        letter_results: dict[str, tuple[str, Literal["green", "yellow", "black"]]] = {}
        for i, div in enumerate(divs):
            aria_label = div.get_attribute("aria-label")
            color: Literal['black', 'yellow', 'green'] = (
                "black" if "errada" in aria_label else
                "yellow" if "local" in aria_label else
                "green"
            )
            letter_results[i] = (
                normalize('NFKD', re.search(r'"([^"]*)"', aria_label).group(1).lower()).encode('ASCII','ignore').decode('ASCII'),
                color
            )
        
        self._logging.var(f"Row {row+1} | Letter results: ", letter_results)  # TODO: Remove
        return letter_results
