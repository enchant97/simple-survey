"use strict";

// hand picked 'nice' colors
const NICE_COLORS = [
    "#b50000", // red
    "#b56400", // orange
    "#a6b500", // yellow
    "#00b500", // green
    "#00b59a", // cyan
    "#008bb5", // light-blue
    "#0000b5", // blue
    "#6100b5", // violet
    "#9100b5", // pink
    "#b5006d", // rose
];

// shuffle using the 'Schwartzian transform', but random
function shuffle(array) {
    return array.map(value => ({ value, sort: Math.random() }))
        .sort((a, b) => a.sort - b.sort)
        .map(({ value }) => value);
}

// returns a random hex color
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
    var colors = NICE_COLORS;

    field_data.options.forEach(option => {
        option_names.push(option.caption);
        vote_counts.push(option.votes.length);
    });

    // if hand picked colors where not enough,
    // randomly generate a color for each missing one
    if (option_names.length > colors.length) {
        while (option_names.length > colors.length) {
            colors.push(get_random_color());
        }
    }

    colors = shuffle(colors);

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
