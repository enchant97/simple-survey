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

function load_votes_pie_chart(field_data, canvas_element) {
    var vote_counts = [];
    var option_names = [];
    var colors = [];

    field_data.options.forEach(option => {
        option_names.push(option.caption);
        vote_counts.push(option.votes.length);
        // TODO replace this with pre-defined colors
        colors.push(get_random_color());
    });

    new Chart(
        canvas_element,
        {
            type: 'doughnut',
            data: {
                labels: option_names,
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
                        display: false,
                    }
                },
                hoverOffset: 10,
            }
        });
}

function load_votes_pie_charts(json_data) {
    json_data.forEach(field => {
        if (field.options.length != 0) {
            let canvas_element = document.getElementById(`chart-vote-${field.id}`);
            load_votes_pie_chart(field, canvas_element);
        }
    });
}

async function load_report_graphs(url) {
    let json_data = await fetch_json(url);
    load_votes_pie_charts(json_data);
}
