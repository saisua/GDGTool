Feature: Enable an extension

Scenario: Crawl a url using rotating proxies
    Given We want to crawl "https://en.wikipedia.org/wiki/Globular_cluster"
    
    When The url is valid
    And  We get the event loop

    Then  A new crawler will be created
    And   We will enable the extension "Rotating proxies"
    And   The crawler will add the urls
    And   The crawler will crawl 0 levels with 1 browser and 5 tabs
    And   The crawler will wait to be closed
    And   The crawler will close