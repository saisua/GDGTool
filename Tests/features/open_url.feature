Feature: Open a url in a new browser

Scenario: Open a url
    Given We want to open "https://duckduckgo.com"
    
    When The url is valid
    And  We get the event loop

    Then  A new browser will be created
    And   The browser will open the url
    And   The browser will wait to be closed
    And   The browser will close