// Load the Visualization API and the corechart package.
google.charts.load('current', {'packages':['corechart']});

// Set a callback to run when the Google Visualization API is loaded.
google.charts.setOnLoadCallback(loadChartData);

function loadChartData() {
    var opts = {sendMethod: 'auto'};
    // Replace the data source URL on next line with your data source URL.
    var query = new google.visualization.Query(
        'https://nest-thermostat-history.appspot.com/loadData', opts);
    
    // Send the query with a callback function.
    query.send(drawChart);
}

// Callback that creates and populates a data table,
// instantiates the pie chart, passes in the data and
// draws it.
function drawChart(response) {
    if (response.isError()) {
        alert('Error in query: ' + response.getMessage() + ' ' +
              response.getDetailedMessage());
        return;
    }
    
    var data = response.getDataTable();
    
    // Set chart options
    var options = {'title':'Readings',
                   'width':400,
                   'height':300};

    // Instantiate and draw our chart, passing in some options.
    var chart = new google.visualization.LineChart(document.getElementById('chart_div'));
    chart.draw(data, options);
}
