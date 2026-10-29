
*** Settings ***
Library    SeleniumLibrary
Test Teardown    Close All Browsers

*** Test Cases ***
Chrome Smoke Test
    Open Browser    about:blank    Chrome
    ${title}=    Execute Javascript    return document.title
    Log To Console    Chrome and JavaScript work
    Sleep    3s
