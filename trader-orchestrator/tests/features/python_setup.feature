Feature: Python Environment Setup
  As a developer
  I want to set up a Python trading environment
  So that I can automate trading strategies

  Scenario: Fresh clone and install
    Given I have cloned the repository
    When I run "poetry install"
    Then all dependencies are installed
    And I can import "ib_insync"
    And I can import "yaml"
    And I can import "pytest"
    And I can import "pytest_bdd"
    And I can import "flake8"
    And I can import "black"

  Scenario: Config file exists
    Given the repository root
    When I list files
    Then "config.yaml" should be present
    And it should contain IBKR connection settings
    And it should contain strategy parameters 