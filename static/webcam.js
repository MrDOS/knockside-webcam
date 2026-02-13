var DISPLAY_FORMAT = 'jpg';

var SECONDS_PER_DAY = 86400;
var SECONDS_PER_QUARTER = SECONDS_PER_DAY / 4;
var DISPLAY_RANGE = SECONDS_PER_DAY * 2;

var images = [];

function loadWebcamImage(image) {
    var day = Math.floor(image / SECONDS_PER_DAY) * SECONDS_PER_DAY;
    var backgroundImage = 'url("' + COMPRESSED_PATH + '/' + day + '/' + SITE_NAME.toLowerCase() + '-' + image.toString() + '.' + DISPLAY_FORMAT + '")';
    if (document.documentElement.style.backgroundImage != backgroundImage) {
        document.documentElement.style.backgroundImage = backgroundImage;
        document.getElementById('when').innerHTML = new Date(image * 1000);
    }
}

function selectWebcamImage(event) {
    var index = parseInt(event.target.value);

    if (index < 0 || index >= images.length) {
        return;
    }

    loadWebcamImage(images[index]);
}

document.getElementById('selector').addEventListener('input', selectWebcamImage);

function loadLatestWebcamImages() {
    var req = new XMLHttpRequest();
    req.addEventListener('load', function () {
        allImages = JSON.parse(this.response).map(s => parseInt(s));
        // The time 48 hours before the latest image.
        var cutoff = allImages[allImages.length - 1] - DISPLAY_RANGE;
        // All images captured within 48 hours of the newest image.
        var newImages = allImages.filter(t => t >= cutoff);

        if (newImages.toString() == images.toString()) {
            // Manifest is unchanged.
            return;
        }

        images = newImages;

        var quarters = document.getElementById('quarters');
        quarters.innerHTML = '';

        var nextQuarter = Math.floor(cutoff / SECONDS_PER_QUARTER) * SECONDS_PER_QUARTER + SECONDS_PER_QUARTER;
        for (var i = 0; i < images.length; ++i) {
            if (images[i] < nextQuarter) {
                continue;
            }

            var tickOption = document.createElement('option');
            tickOption.value = i;
            quarters.appendChild(tickOption);

            nextQuarter += SECONDS_PER_QUARTER;
        }

        var selector = document.getElementById('selector');
        selector.min = 0;
        selector.max = images.length - 1;
        selector.value = images.length - 1;

        loadWebcamImage(images[images.length - 1]);
    });
    req.open('GET', COMPRESSED_PATH + '/manifest.json');
    req.send();
}
window.setInterval(loadLatestWebcamImages, 60 * 1000);
loadLatestWebcamImages();

document.getElementsByTagName('title')[0].innerText = SITE_NAME;
