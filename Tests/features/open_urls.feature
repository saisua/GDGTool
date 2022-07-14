Feature: Open a url in a new browser

Scenario: Open urls
    Given We want to open urls
        | url |
        | https://duckduckgo.com |
        | https://github.com |

    When The urls are valid
    And  We get the event loop

    Then  A new browser will be created
    And   The browser will open the urls
    And   The browser will wait to be closed
    And   The browser will close