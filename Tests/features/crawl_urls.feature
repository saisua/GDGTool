Feature: Crawl urls in a new browser

Scenario: Crawl urls
    Given We want to crawl urls
        | url |
        | https://duckduckgo.com |
        | https://github.com |
    
    When The urls are valid
    And  We get the event loop

    Then  A new crawler will be created
    And   The crawler will add the urls
    And   The crawler will crawl 0 levels with 1 browser and 5 tabs
    And   The crawler will wait to be closed
    And   The crawler will close