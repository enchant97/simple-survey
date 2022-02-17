"use strict";

function get_random_color() {
    let color = '#';
    for (let i = 0; i < 6; i++) {
        const random = Math.random();
        const bit = (random * 16) | 0;
        color += (bit).toString(16);
    };
    return color;
}

async function fetch_json(url) {
    // TODO error handling
    const resp = await fetch(url);
    return await resp.json();
}

function load_votes_pie_chart(json_data, canvas_element) {
    var vote_counts = [];
    var choice_names = [];
    var colors = [];

    json_data.forEach(choice => {
        choice_names.push(choice.caption);
        vote_counts.push(choice.votes.length);
        // TODO replace this with pre-defined colors
        colors.push(get_random_color());
    });

    new Chart(
        canvas_element,
        {
            type: 'doughnut',
            data: {
                labels: choice_names,
                datasets: [
                    {
                        data: vote_counts,
                        backgroundColor: colors,
                        borderColor: "transparent",
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    title: {
                        display: true,
                        text: 'All Votes'
                    }
                },
                hoverOffset: 10,
            }
        });
}

async function load_report_graphs(url) {
    let chart_votes_pie_canvas = document.getElementById("chart-votes-pie");
    let json_data = await fetch_json(url);

    load_votes_pie_chart(json_data, chart_votes_pie_canvas);
}
