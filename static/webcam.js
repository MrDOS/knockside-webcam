/* No feature flag for WebP support, and the fast/easy checking techniques
 * (e.g., https://stackoverflow.com/a/27232658/640170) don't work on Firefox,
 * so we'll do the dumb thing and sniff the user agent. */
var DISPLAY_FORMAT = window.navigator.userAgent.toLowerCase().indexOf('safari') != -1 ? 'jpg' : 'webp';

function loadLatestWebcamImage() {
    var req = new XMLHttpRequest();
    req.addEventListener('load', function () {
        var images = JSON.parse(this.response);
        var latestImage = images[images.length - 1];
        var backgroundImage = 'url("' + COMPRESSED_PATH + '/' + SITE_NAME.toLowerCase() + '-' + latestImage + '.' + DISPLAY_FORMAT + '")';
        if (document.documentElement.style.backgroundImage != backgroundImage) {
            document.documentElement.style.backgroundImage = backgroundImage;
            document.getElementById('when').innerHTML = new Date(parseInt(latestImage) * 1000);
        }
    });
    req.open('GET', COMPRESSED_PATH + '/manifest.json');
    req.send();
}
window.setInterval(loadLatestWebcamImage, 60 * 1000);
loadLatestWebcamImage();

document.getElementsByTagName('title')[0].innerText = SITE_NAME;
