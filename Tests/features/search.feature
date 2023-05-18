Feature: Search on the internet

Scenario: Search
    When  We get the event loop

    Then  A new crawler will be created
    And   We will setup a search for "Cork"
    And   The crawler will crawl 1 levels with 1 browser and 5 tabs
    And   The crawler will wait to be closed
    And   The browser will close

Scenario: Search an image
    When  We get the event loop

    Then  A new crawler will be created
    And   We will setup a search for "Cork" in images
    And   The crawler will crawl 1 levels with 1 browser and 5 tabs
    And   The crawler will wait to be closed
    And   The browser will close

Scenario: Search and get keywords
    When  We get the event loop

    Then  A new crawler will be created
    And   We will setup a search for "Cork"
    And   We will setup the plugin "Keywords"
    And   The crawler will crawl 1 levels with 1 browser and 5 tabs
    And   The crawler will wait to be closed
    And   The browser will close