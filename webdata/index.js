var container = document.getElementById('container');
var imagestreamUrl = `/imagestream${window.location.search}`;
var imageElement = document.createElement('img');
container.innerHTML = '';
container.appendChild(imageElement);
setTimeout(function () {
    imageElement.src = imagestreamUrl;
});
