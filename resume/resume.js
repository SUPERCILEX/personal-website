const request = downloadResume();
keepPageInLoadingStateForever();

function downloadResume() {
    const request = new XMLHttpRequest();
    request.responseType = 'blob';
    request.open(
        "GET",
        "https://docs.google.com/document/d/11sHvpwRaWoafEr2k8w5uXaJB0_VuMCtSxQNsErnpet0/export?format=pdf"
    );
    request.onload = onDownloaded;
    request.send(null);
    return request;
}

function onDownloaded() {
    const link = document.createElement('a');
    link.href = window.URL.createObjectURL(request.response);
    link.download = "AlexSaveau.pdf";
    link.click();

    window.location.replace("/");
}

function keepPageInLoadingStateForever() {
    const f = document.createElement('iframe');
    f.onload = function () {
        f.contentWindow.location.reload();
    };
    f.src = 'about:blank';
    f.style.display = 'none';
    document.body.appendChild(f);
}
