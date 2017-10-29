// MIT License

// Copyright (c) 2017 kirk25

// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:

// The above copyright notice and this permission notice shall be included in
// all copies or substantial portions of the Software.

// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.

// Load the Visualization API and the corechart package.
google.charts.load('current', {'packages':['corechart']});

// Set a callback to run when the Google Visualization API is loaded.
google.charts.setOnLoadCallback(loadChartData);

function loadChartData() {
    for (i = 0; i < devices.length; i++) { 
        var device = devices[i];
        document.getElementById("chart_div_" + device).innerHTML = "Loading...";
    
        var opts = {sendMethod: 'auto'};
        var url = loadDataURL + "?device=" + device;
        // Replace the data source URL on next line with your data source URL.
        var query = new google.visualization.Query(url, opts);
    
        // Send the query with a callback function.
        query.send(drawChart.bind({device: device}));
    }
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

    // Convert to Pacific time.
    // TODO: stop hard-coding the offset.  Also make it work.
    var formatter = new google.visualization.DateFormat({timeZone: -7});
    formatter.format(data, 0)
    
    // Set chart options
    var options = {'title':'Readings',
                   'width':600,
                   'height':300};

    // Instantiate and draw our chart, passing in some options.
    var chart = new google.visualization.LineChart(document.getElementById("chart_div_" + this.device));
    chart.draw(data, options);
}
