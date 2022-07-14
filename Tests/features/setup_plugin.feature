Feature: Setup the plugin summary

Scenario: Generate the summary of a url
    Given We want to crawl "https://en.wikipedia.org/wiki/Globular_cluster"
    
    When The url is valid
    And  We get the event loop

    Then  A new crawler will be created
    And   We will setup the plugin "Summary"
    And   The crawler will add the urls
    And   The crawler will crawl 0 levels with 1 browser and 5 tabs
    And   The crawler will wait to be closed
    And   The crawler will close