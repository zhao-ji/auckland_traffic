var color = Chart.helpers.color;
var config = {
	type: 'line',
	data: {
		datasets: [{
			label: 'Home to City',
			backgroundColor: color(window.chartColors.blue).alpha(0.5).rgbString(),
			borderColor: window.chartColors.blue,
			fill: false,
			data: [],
		}]
	},
	options: {
		responsive: true,
		title: {
			display: true,
			text: 'Auckland Traffic Monitoring'
		},
		scales: {
			xAxes: [{
				type: 'time',
                time: {
                    displayFormats: {
                        hour: "DD hA"
                    }
                },
				display: true,
				scaleLabel: {
					display: true,
					labelString: 'Datetime (h)'
				},
				ticks: {
					major: {
						fontStyle: 'bold',
						fontColor: '#FF0000'
					}
				}
			}],
			yAxes: [{
				display: true,
				scaleLabel: {
					display: true,
					labelString: 'Duration (min)'
				}
			}]
		}
	}
};

function putDataIntoChart(chartData, initial=false) {
    if (initial) {
        var ctx = document.getElementById('canvas').getContext('2d');
        config.data.datasets = chartData;
        window.myLine = new Chart(ctx, config);
    } else {
        config.data.datasets = chartData;
        window.myLine.update();
    }
}

function updateChart(hour=6, initial=false) {
    let timeFrom = new Date().getTime();
    timeFrom = Math.round(timeFrom/1000) - hour * 3600;
    loadJSON("http://traffic.minganci.org/api/all?time_from=" + timeFrom, function (data){
        let chartData = [];
        let colorIndex = 0;

        Object.keys(data).forEach(origin => {
            Object.keys(data[origin]).forEach(destination => {
                let pointForChart = data[origin][destination].map(point => {
                    let date = new Date(point[0] + " UTC");
                    return {
                        x: date,
                        y: Math.round(point[1]/60)
                    };
                });
                let chartColor = window.chartColors[Object.keys(window.chartColors)[colorIndex]]
                chartData.push({
                    label: origin + " to " + destination,
                    backgroundColor: color(chartColor).alpha(0.5).rgbString(),
                    borderColor: chartColor,
                    fill: false,
                    data: pointForChart,
                });
                colorIndex += 1;
            })
        });

        putDataIntoChart(chartData, initial=initial);
    });
}

window.onload = function() {
    updateChart(3, initial=true);
};
document.getElementById('12hours').addEventListener('click', function() {
    updateChart(12);
});
document.getElementById('day').addEventListener('click', function() {
    updateChart(24);
});
document.getElementById('3days').addEventListener('click', function() {
    updateChart(72);
});
document.getElementById('week').addEventListener('click', function() {
    updateChart(24*7);
});
