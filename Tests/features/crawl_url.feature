Feature: Crawl an url in a new browser

Scenario: Crawl an url
    Given We want to crawl "https://duckduckgo.com"
    
    When The url is valid
    And  We get the event loop

    Then  A new crawler will be created
    And   The crawler will add the urls
    And   The crawler will crawl 1 levels with 1 browser and 5 tabs
    And   The crawler will wait to be closed
    And   The crawler will close