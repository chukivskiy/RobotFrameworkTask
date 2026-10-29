
*** Settings ***
Library    SeleniumLibrary
Library    PlotlyParquetLibrary.py
Test Teardown    Close All Browsers

*** Variables ***
${REPORT}     ${CURDIR}${/}report.html
${DATASET}    ${CURDIR}${/}facility_type_avg_time_spent_per_visit_date

*** Test Cases ***
Plotly Report Matches Parquet Dataset
    ${url}=    Evaluate    pathlib.Path(r'''${REPORT}''').resolve().as_uri()    modules=pathlib

    Log To Console    STEP 1: Opening Chrome
    Open Browser    about:blank    Chrome

    Log To Console    STEP 2: Opening HTML report
    Go To    ${url}

    Log To Console    STEP 3: Waiting for Plotly table
    Wait Until Page Contains Element    css:.js-plotly-plot    timeout=60s
    Wait Until Keyword Succeeds    20x    2s    Plotly Table Should Be Ready

    Log To Console    STEP 4: Extracting HTML data
    ${data}=    Execute Javascript
    ...    const graph = document.querySelector('.js-plotly-plot');
    ...    const table = graph?.data?.find(trace => trace.type === 'table');
    ...    if (!table) throw new Error('Plotly table not found');
    ...    const headers = table.header.values.map(String);
    ...    const columns = table.cells.values;
    ...    if (columns.length !== headers.length) throw new Error('Column count mismatch');
    ...    const rows = columns.length ? Array.from({length: columns[0].length}, (_, i) => columns.map(c => c[i])) : [];
    ...    return {headers: headers, rows: rows};

    Log To Console    STEP 5: Comparing with Parquet
    Compare Plotly Data To Parquet    ${data}[headers]    ${data}[rows]    ${DATASET}

    Log To Console    STEP 6: All data matches!

*** Keywords ***
Plotly Table Should Be Ready
    ${ready}=    Execute Javascript    return !!document.querySelector('.js-plotly-plot')?.data?.some(t => t.type === 'table')
    Should Be True    ${ready}
