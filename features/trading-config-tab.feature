Feature: Trading Configuration Tab
  As a trader
  I want to adjust my trading strategy parameters
  So that I can optimize my trading performance

  Background:
    Given the application is running
    And I navigate to the "Strategy Config" tab

  Scenario: Render dynamic fields including execution parameters
    Given schemaStore has execution properties [max_bid_ask_distance, order_type]
    When the Trading Config Tab is rendered
    Then input fields for "Maximum % Distance between Bid and Ask" and a dropdown for "Order Type" appear

  Scenario: Validate bid-ask distance
    Given user inputs a max_bid_ask_distance of -1
    Then an inline validation error is displayed
    And the Save button is disabled

  Scenario: Save execution parameters
    Given valid execution parameters in configStore
    When user clicks "Save Configuration"
    Then saveConfig receives correct JSON including max_bid_ask_distance and order_type
    And a success message is displayed

  Scenario: Display error message on save failure
    Given the save operation will fail
    When user clicks "Save Configuration"
    Then an error message is displayed
    And the form remains editable

  Scenario: Order type dropdown shows available options
    Given schemaStore has order_type enum with ["Market", "Limit", "MidPrice"]
    When the Trading Config Tab is rendered
    Then the Order Type dropdown shows all three options 